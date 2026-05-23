import time
import json
import uuid
import re
import os
import sys
import asyncio
from pathlib import Path

# Ensure workspace root is on sys.path so top-level packages like `shared`
# and `services` can be imported when running this module from the
# `services/orchestrator` folder (e.g. `uvicorn app.main`). This makes the
# orchestrator execution robust in local dev without requiring PYTHONPATH.
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.utils.logger import logger
from app.config import get_settings
from app.schemas import ChatRequest, ChatResponse, ExecutionTrace, TraceStep, ToolCall, PipelineData, PipelineNode, PipelineEdge
from app.executor import execute_tool
from app.core.tracker import get_trace, init_trace, emit_trace_event
from app.tool_registry import registry as tool_registry
from app.core.tools import OrchestratorRequest
from services.orchestrator.app.llm.groq_client import GroqRouter
from services.orchestrator.app.llm.mistral_client import MistralReasoner
from shared.config import SharedConfig


PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z0-9_.\[\]-]+)\}")

app = FastAPI(title="Central Orchestrator")

# --- STARTUP BANNER ---
BANNER = r"""
  █████╗ ████████╗██╗      █████╗ ███████╗
 ██╔══██╗╚══██╔══╝██║     ██╔══██╗██╔════╝
 ███████║   ██║   ██║     ███████║███████╗
 ██╔══██║   ██║   ██║     ██╔══██║╚════██║
 ██║  ██║   ██║   ███████╗██║  ██║███████║
 ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝
         AI ORCHESTRATION ENGINE v2.0
"""

@app.on_event("startup")
async def startup_event():
    """
    Initialize ATLAS orchestrator on startup.
    - Sets up LLM providers (routing, formatting)
    - Performs health checks on all services
    - Logs configuration for debugging
    """
    logger.info(BANNER)
    logger.info("Initializing ATLAS Multi-Service Orchestrator...")
    
    # Load configuration
    config = SharedConfig()
    settings = get_settings()
    
    logger.info(f"Environment: {config.env}")
    logger.info(f"Log Level: {config.log_level}")
    
    # Initialize cloud LLM clients (Groq routing + Mistral fallback)
    logger.info("Initializing cloud LLM clients (Groq + Mistral)...")
    try:
        # Groq router
        groq_api_key = config.llm.routing_api_key or config.llm.openrouter_api_key or os.getenv("GROQ_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        groq_base_url = config.llm.openrouter_base_url if config.llm.openrouter_api_key and not config.llm.routing_api_key else os.getenv("GROQ_API_URL")
        app.state.groq = GroqRouter(api_key=groq_api_key, model=config.llm.routing_model, base_url=groq_base_url)
        routing_ok = await app.state.groq.health_check()
        if routing_ok:
            logger.info(f"✓ Groq router initialized: {config.llm.routing_model}")
        else:
            logger.warning("⚠ Groq router health check failed")

        # Mistral reasoner (fallback / heavy reasoning)
        mistral_key = config.llm.mistral_api_key or os.getenv("MISTRAL_API_KEY")
        app.state.mistral = MistralReasoner(api_key=mistral_key, model=config.llm.reasoning_model)
        mistral_ok = await app.state.mistral.health_check()
        if mistral_ok:
            logger.info(f"✓ Mistral reasoner initialized: {config.llm.reasoning_model}")
        else:
            logger.warning("⚠ Mistral reasoner health check failed")

    except Exception as e:
        logger.error(f"Failed to initialize cloud LLM clients: {e}")
        raise
    
    # Log service URLs
    logger.info(f"Google MCP URL: {settings.gmail_mcp_base_url}")
    logger.info(f"Memory Service URL: {settings.memory_service_url}")
    logger.info(f"Orchestrator listening on {settings.orchestrator_host}:{settings.orchestrator_port}")
    logger.info("Ready for requests.")

# Instrumentation & CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        - status: "healthy" or "degraded"
        - service: "orchestrator"
        - llm_providers: LLM health status
        - timestamp: current time
    """
    health_info = {
        "status": "healthy",
        "service": "orchestrator",
        "timestamp": time.time(),
        "llm_providers": {
            "groq": {"healthy": False},
            "mistral": {"healthy": False}
        }
    }
    
    # Check routing LLM
    if hasattr(app.state, "groq"):
        try:
            health_info["llm_providers"]["groq"]["healthy"] = await app.state.groq.health_check()
        except Exception as e:
            logger.warning(f"Groq health check failed: {e}")
            health_info["llm_providers"]["groq"]["healthy"] = False
            health_info["status"] = "degraded"
    
    # Check formatting LLM
    if hasattr(app.state, "mistral"):
        try:
            health_info["llm_providers"]["mistral"]["healthy"] = await app.state.mistral.health_check()
        except Exception as e:
            logger.warning(f"Mistral health check failed: {e}")
            health_info["llm_providers"]["mistral"]["healthy"] = False
            health_info["status"] = "degraded"
    
    return health_info


def _get_user_query(chat_request: ChatRequest) -> str:
    return (chat_request.message or getattr(chat_request, "query", None) or "").strip()


def _build_tool_registry_prompt() -> str:
    return tool_registry.tool_descriptions_for_prompt()


def _resolve_placeholder_value(results: Dict[str, Any], placeholder: str) -> Any:
    current: Any = results
    for token in placeholder.split('.'):
        token_match = re.match(r'^([^[\]]+)((?:\[\d+\])*)$', token)
        if not token_match:
            raise KeyError(placeholder)

        key = token_match.group(1)
        indices = [int(match) for match in re.findall(r'\[(\d+)\]', token_match.group(2))]

        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            raise KeyError(placeholder)

        for index in indices:
            if isinstance(current, list) and 0 <= index < len(current):
                current = current[index]
            else:
                raise KeyError(placeholder)

    return current


def _substitute_placeholders(value: Any, results: Dict[str, Any]) -> tuple[Any, set[str]]:
    unresolved: set[str] = set()

    if isinstance(value, dict):
        substituted: Dict[str, Any] = {}
        for key, item in value.items():
            substituted_item, item_unresolved = _substitute_placeholders(item, results)
            substituted[key] = substituted_item
            unresolved.update(item_unresolved)
        return substituted, unresolved

    if isinstance(value, list):
        substituted_list = []
        for item in value:
            substituted_item, item_unresolved = _substitute_placeholders(item, results)
            substituted_list.append(substituted_item)
            unresolved.update(item_unresolved)
        return substituted_list, unresolved

    if not isinstance(value, str):
        return value, unresolved

    matches = list(PLACEHOLDER_PATTERN.finditer(value))
    if not matches:
        return value, unresolved

    if len(matches) == 1 and matches[0].span() == (0, len(value)):
        placeholder = matches[0].group(1)
        try:
            return _resolve_placeholder_value(results, placeholder), unresolved
        except (KeyError, IndexError, TypeError):
            unresolved.add(placeholder)
            return value, unresolved

    substituted_text = value
    for match in matches:
        placeholder = match.group(1)
        try:
            resolved = _resolve_placeholder_value(results, placeholder)
        except (KeyError, IndexError, TypeError):
            unresolved.add(placeholder)
            continue

        if isinstance(resolved, (dict, list)):
            replacement = json.dumps(resolved, ensure_ascii=False, default=str)
        else:
            replacement = str(resolved)

        substituted_text = substituted_text.replace(f"{{{placeholder}}}", replacement)

    return substituted_text, unresolved


async def _execute_planned_tool(tool_call, user_id: str, request_id: str, trace_id: str, original_params: dict = None):
    logger.info(f"[{request_id}] Executing tool {tool_call.name} with params: {tool_call.params}")
    emit_trace_event(trace_id, f"{request_id}-{tool_call.name}", "running", node_type="mcp_tool", name=tool_call.name, inputs=tool_call.params, meta={"tool_name": tool_call.name, "original_params": original_params or tool_call.params})
    t0 = time.perf_counter()
    schema_tool = ToolCall(tool=tool_call.name, arguments=tool_call.params)
    result = await execute_tool(
        schema_tool,
        gmail_user_id=user_id,
        drive_user_id=user_id,
        calendar_user_id=user_id,
    )
    result._duration_ms = (time.perf_counter() - t0) * 1000
    if getattr(result, "success", False):
        emit_trace_event(trace_id, f"{request_id}-{tool_call.name}", "success", node_type="mcp_tool", name=tool_call.name, outputs=result.data, latency=result._duration_ms)
    else:
        err = getattr(result, "error", "Tool failed")
        emit_trace_event(trace_id, f"{request_id}-{tool_call.name}", "failed", node_type="mcp_tool", name=tool_call.name, error=err, latency=result._duration_ms)
    return result


def build_pipeline_graph(tools, results: dict, total_ms: float = 0.0) -> PipelineData:
    """Build pipeline visualization from executed tools and their results."""
    nodes: list[PipelineNode] = []
    edges: list[PipelineEdge] = []
    tool_names = {t.name for t in tools}

    for tool in tools:
        result = results.get(tool.name, {})
        has_error = isinstance(result, dict) and "error" in result
        nodes.append(PipelineNode(
            id=tool.name,
            label=tool.name.replace("_", " ").title(),
            status="error" if has_error else "success",
            duration=results.get(f"_dur_{tool.name}", 0.0),
            error=result.get("error") if has_error else None,
        ))

    # Add dependency edges detected from placeholder refs in params
    existing = set()
    for tool in tools:
        params_str = json.dumps(tool.params, default=str)
        refs = re.findall(r'\{([A-Za-z0-9_]+)\.', params_str)
        for ref in refs:
            if ref in tool_names and ref != tool.name and (ref, tool.name) not in existing:
                edges.append(PipelineEdge(source=ref, target=tool.name, type="dependency"))
                existing.add((ref, tool.name))

    return PipelineData(nodes=nodes, edges=edges, execution_time_ms=total_ms)


async def _execute_planned_tools(tools, user_id: str, request_id: str, trace_id: str) -> tuple[Dict[str, Any], Dict[str, float]]:
    if not tools:
        return {}, {}

    compiled: Dict[str, Any] = {}
    timings: Dict[str, float] = {}
    failed_tools: set[str] = set()

    pending = list(tools)
    while pending:
        ready_tools = []
        pending_names = {tool_call.name for tool_call in pending}

        for tool_call in pending:
            _, unresolved_placeholders = _substitute_placeholders(tool_call.params, compiled)
            unresolved_dependencies = {
                placeholder.split('.')[0]
                for placeholder in unresolved_placeholders
                if placeholder.split('.')[0] in pending_names or placeholder.split('.')[0] in failed_tools
            }
            if unresolved_dependencies:
                continue
            ready_tools.append(tool_call)

        if not ready_tools:
            tool_call = pending.pop(0)
            resolved_params, unresolved_placeholders = _substitute_placeholders(tool_call.params, compiled)
            failed_dependencies = sorted(
                {
                    placeholder.split('.')[0]
                    for placeholder in unresolved_placeholders
                    if placeholder.split('.')[0] in failed_tools
                }
            )

            if failed_dependencies:
                error_message = f"Dependency failed: {', '.join(failed_dependencies)}"
                logger.error(f"[{request_id}] Skipping {tool_call.name}: {error_message}")
                compiled[tool_call.name] = {"error": error_message}
                failed_tools.add(tool_call.name)
                continue

            if unresolved_placeholders:
                logger.warning(f"[{request_id}] Executing {tool_call.name} with unresolved placeholders: {sorted(unresolved_placeholders)}")

            result = await _execute_planned_tool(
                type(tool_call)(name=tool_call.name, params=resolved_params),
                user_id,
                request_id,
                trace_id,
                original_params=tool_call.params
            )
            dur = getattr(result, '_duration_ms', 0.0)
            timings[tool_call.name] = dur
            if getattr(result, "success", False):
                compiled[tool_call.name] = result.data
            else:
                compiled[tool_call.name] = {"error": getattr(result, "error", "Tool failed")}
                failed_tools.add(tool_call.name)
            continue

        logger.info(
            f"[{request_id}] Executing {len(ready_tools)} independent tools in parallel: {', '.join(tool_call.name for tool_call in ready_tools)}"
        )
        for tool_call in ready_tools:
            pending.remove(tool_call)

        async def _run_ready_tool(tool_call):
            resolved_params, unresolved_placeholders = _substitute_placeholders(tool_call.params, compiled)
            if unresolved_placeholders:
                logger.warning(
                    f"[{request_id}] {tool_call.name} still has unresolved placeholders before execution: {sorted(unresolved_placeholders)}"
                )
            return await _execute_planned_tool(
                type(tool_call)(name=tool_call.name, params=resolved_params),
                user_id,
                request_id,
                trace_id,
                original_params=tool_call.params
            )

        batch_results = await asyncio.gather(*[_run_ready_tool(tool_call) for tool_call in ready_tools], return_exceptions=True)

        for tool_call, result in zip(ready_tools, batch_results):
            if isinstance(result, Exception):
                compiled[tool_call.name] = {"error": str(result)}
                timings[tool_call.name] = 0.0
                failed_tools.add(tool_call.name)
            else:
                timings[tool_call.name] = getattr(result, '_duration_ms', 0.0)
                if getattr(result, "success", False):
                    compiled[tool_call.name] = result.data
                else:
                    compiled[tool_call.name] = {"error": getattr(result, "error", "Tool failed")}
                    failed_tools.add(tool_call.name)

    return compiled, timings

@app.get("/api/profile")
async def get_profile(
    gmail_user_id: str = Query(..., alias="gmail_id"),
    drive_user_id: str = Query(..., alias="drive_id")
):
    """Bridge for frontend to get basic profile if needed"""
    return {"gmail": gmail_user_id, "drive": drive_user_id}

@app.get("/api/traces/recent")
async def fetch_recent_traces(limit: int = 10):
    from app.core.tracker import list_recent_traces
    return list_recent_traces(limit)

@app.get("/api/trace/{execution_id}")
async def fetch_trace(execution_id: str):
    trace = get_trace(execution_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace

@app.get("/trace/{execution_id}/graph")
async def fetch_graph(execution_id: str):
    logger.info(f"[API] Graph fetch requested for: {execution_id}")
    from app.core.tracker import get_graph_data
    data = get_graph_data(execution_id)
    if not data["nodes"]:
        logger.warning(f"[API] Graph for {execution_id} is EMPTY")
    return data

@app.get("/trace/{execution_id}/timeline")
async def fetch_timeline(execution_id: str):
    logger.info(f"[API] Timeline fetch requested for: {execution_id}")
    from app.core.tracker import get_timeline_data
    return get_timeline_data(execution_id)

@app.post("/trace/{execution_id}/replay")
async def replay_trace(execution_id: str):
    return {"new_execution_id": f"replay_{execution_id}_{int(time.time())}"}

@app.post("/trace/{execution_id}/simulate_failure")
async def simulate_failure(execution_id: str, payload: dict):
    logger.info(f"[SIMULATION] Configured failure for {payload.get('node_id')} in {execution_id}")
    return {"status": "configured"}

@app.post("/chat")
async def chat_endpoint(chat_request: ChatRequest, request: Request):
    session_id = chat_request.session_id or str(uuid.uuid4())
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    user_id = request.headers.get("X-User-Id") or chat_request.user_id or chat_request.gmail_user_id or "anonymous"
    wall_start = time.perf_counter()

    query = _get_user_query(chat_request)
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    init_trace(request_id, query=query)
    trace = ExecutionTrace(steps=[], status="running")

    logger.info(f"[{request_id}] Chat query from {user_id}: {query}")

    try:
        planning_payload = {tool.name: {"description": tool.description, "params": list(tool.input_schema.get("properties", {}).keys())} for tool in tool_registry.all_tools()}

        trace.steps.append(
            TraceStep(
                id=f"{request_id}-planner",
                title="Plan Tools",
                description="Groq planning step",
                status="running",
            )
        )

        emit_trace_event(request_id, f"{request_id}-planner", "running", node_type="planner", name="Plan Tools")
        plan_dict = await app.state.groq.plan_tools(query=query, tool_registry=planning_payload)
        plan = OrchestratorRequest(**plan_dict)
        emit_trace_event(request_id, f"{request_id}-planner", "success", node_type="planner", name="Plan Tools", outputs=plan_dict)

        trace.steps[-1].status = "success"
        trace.steps[-1].details = plan.reasoning

        logger.info(f"[{request_id}] Groq plan: {plan_dict}")

        results, timings = await _execute_planned_tools(plan.tools, user_id, request_id, request_id)

        for tool_call in plan.tools:
            result_value = results.get(tool_call.name, {})
            trace.steps.append(
                TraceStep(
                    id=f"{request_id}-{tool_call.name}",
                    title=f"Tool: {tool_call.name}",
                    description=json.dumps(tool_call.params, default=str),
                    status="success" if not isinstance(result_value, dict) or "error" not in result_value else "failed",
                    details=json.dumps(result_value, default=str)[:1500],
                )
            )

        emit_trace_event(request_id, f"{request_id}-synthesis", "running", node_type="synthesis", name="Synthesize Response")
        final_response = await app.state.groq.synthesize_response(
            original_query=query,
            tool_results=results,
            reasoning=plan.reasoning,
        )
        emit_trace_event(request_id, f"{request_id}-synthesis", "success", node_type="synthesis", name="Synthesize Response", outputs={"response": final_response})

        trace.steps.append(
            TraceStep(
                id=f"{request_id}-synthesis",
                title="Synthesize Response",
                description="Groq response generation",
                status="success",
                details=final_response[:1500],
            )
        )

        total_ms = (time.perf_counter() - wall_start) * 1000
        trace.status = "success"
        trace.total_time_ms = total_ms
        pipeline = build_pipeline_graph(plan.tools, results, total_ms)
        
        logger.info(f"[{request_id}] Pipeline graph: {pipeline.model_dump_json()}")
        
        response_obj = ChatResponse(
            response=final_response,
            response_type="success",
            trace=trace,
            session_id=session_id,
            mode="json-router",
            tool_used=", ".join([tool.name for tool in plan.tools]) if plan.tools else None,
            tool_result=results,
            pipeline=pipeline,
        )
        
        logger.info(f"[{request_id}] Response includes pipeline: {response_obj.pipeline is not None}")
        
        return response_obj
    except Exception as e:
        logger.error(f"[{request_id}] Chat failed: {e}", exc_info=True)
        trace.status = "error"
        trace.total_time_ms = (time.perf_counter() - wall_start) * 1000
        return ChatResponse(
            response=f"Error: {str(e)}",
            response_type="error",
            trace=trace,
            session_id=session_id,
            mode="json-router",
        )
