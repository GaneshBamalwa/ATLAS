import time
import json
import uuid
import re
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.utils.logger import logger
from app.config import get_settings
from app.schemas import ChatRequest, ChatResponse, ExecutionTrace, TraceStep, ToolCall
from app.executor import execute_tool
from app.router import route_query, extract_facts
from app.graph_runtime.engine import run_workflow
from app.core.tracker import get_trace, init_trace, emit_trace_event

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
    print(BANNER)
    logger.info("Initializing ATLAS Multi-Service Orchestrator...")
    logger.info(f"LLM Engine: {settings.llm_model}")
    logger.info(f"Targeting MCP: {settings.gmail_mcp_base_url}")
    logger.info("Ready for requests on port 9000.")

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
async def health():
    return {"status": "healthy", "service": "orchestrator"}

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
    wall_start = time.perf_counter()
    
    # Initialize global trace store for dashboard
    init_trace(session_id)
    
    trace = ExecutionTrace(
        steps=[],
        status="running"
    )

    # Check for X-Use-Graph header for engine selection
    use_graph_header = request.headers.get("X-Use-Graph", "false").lower() == "true"
    use_langgraph = (chat_request.engine == "langgraph") or use_graph_header

    # ─── LangGraph Engine Path ────────────────────────────────────────────────
    if use_langgraph:
        logger.info(f"[CHAT] Using LangGraph engine (Header: {use_graph_header})...")
        try:
            user_context = {
                "gmail_user_id": chat_request.gmail_user_id,
                "drive_user_id": chat_request.drive_user_id,
                "calendar_user_id": chat_request.calendar_user_id
            }
            print(f"[ENGINE] Routing to LANGRAPH engine (Session: {session_id})")
            result = await run_workflow(chat_request.message, history=chat_request.history, context=user_context, execution_id=session_id)
            
            # Re-fetch the trace from tracker to send back enriched steps
            from app.core.tracker import get_trace
            global_trace = get_trace(session_id)
            if global_trace:
                for node in global_trace.nodes:
                    trace.steps.append(TraceStep(
                        id=node.id,
                        title=node.name,
                        description=f"Status: {node.status}",
                        status=node.status if node.status in ["pending", "running", "completed", "success", "failed", "error"] else "completed",
                        details=str(node.outputs or "") if node.status == "success" else node.error
                    ))

            trace.status = "success"
            trace.total_time_ms = (time.perf_counter() - wall_start) * 1000
            return ChatResponse(
                response=result["response"],
                response_type="success",
                trace=trace,
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"[CHAT] LangGraph execution failed: {e}")
            return ChatResponse(response=f"Error: {str(e)}", response_type="error", trace=trace, session_id=session_id)

    # ─── Legacy Reasoning Loop (ReAct / Chaining) ─────────────────────────────
    print(f"[ENGINE] Routing to LEGACY standard engine (Session: {session_id})")
    max_loops = 10
    loop_count = 0
    current_message = chat_request.message
    
    print(f"\n[ORCHESTRATOR] New query: {current_message}")
    print(f"[ORCHESTRATOR] Session ID: {session_id}")
    
    current_history = list(chat_request.history) if chat_request.history else []
    executed_actions = []
    mutative_tools = {"send_email", "add_calendar_event", "delete_calendar_event", "trash_drive_file"}
    
    while loop_count < max_loops:
        loop_count += 1
        
        # 1. Routing Decision
        step_id = f"planner_{loop_count}"
        route_start = time.perf_counter()
        
        emit_trace_event(session_id, step_id, "running", node_type="llm_planner", name="Planning Step")

        decision = await route_query(
            current_message, 
            history=current_history, 
            context={"gmail_user_id": chat_request.gmail_user_id, "drive_user_id": chat_request.drive_user_id}
        )
        
        route_time = (time.perf_counter() - route_start) * 1000
        emit_trace_event(session_id, step_id, "success", outputs={"decision": decision.dict()}, latency=route_time)
        print(f" -> Loop {loop_count}: {decision.dict()}")

        if decision.requires_tool:
            tool_call = decision.tool_call
            for prev in executed_actions:
                if prev["tool_name"] == tool_call.tool and prev["input"] == tool_call.arguments:
                    logger.warning(f"[ORCHESTRATOR] Redundant tool call detected: {tool_call.tool}. Forcing completion.")
                    decision.requires_tool = False
                    decision.response = f"I have already executed {tool_call.tool} and obtained the result. Moving to final summary."
                    break

        if not decision.requires_tool:
            trace.status = "completed"
            trace.total_time_ms = (time.perf_counter() - wall_start) * 1000
            
            # Format the final response using Groq synthesis
            from app.formatter import format_response
            payload = {
                "intent": "final_response",
                "requires_tools": len(executed_actions) > 0,
                "actions": executed_actions,
                "final_result": decision.response or "Process complete.",
                "confidence": 1.0
            }
            final_text = await format_response(payload)
            
            emit_trace_event(session_id, "formatter_final", "success", node_type="formatter", name="Final Response", inputs={"text": final_text})
            return ChatResponse(response=final_text, response_type="success", trace=trace, session_id=session_id)
        
        # 2. Tool Execution (with Replay Safeguard)
        exec_id = f"executor_{tool_call.tool}_{loop_count}"
        step_exec = TraceStep(id=f"step-{loop_count}-exec", title=f"Activity: {tool_call.tool}", description=f"Arguments: {tool_call.arguments}")
        trace.steps.append(step_exec)
        
        emit_trace_event(session_id, exec_id, "running", node_type="mcp_tool", name=f"Tool: {tool_call.tool}", inputs=tool_call.arguments)
        print(f" -> Executing tool: {tool_call.tool} with args: {tool_call.arguments}")

        # Normal Execute
        exec_start = time.perf_counter()

        tool_response = await execute_tool(
            tool_call, 
            gmail_user_id=chat_request.gmail_user_id, 
            drive_user_id=chat_request.drive_user_id, 
            calendar_user_id=chat_request.calendar_user_id
        )
        exec_time = (time.perf_counter() - exec_start) * 1000
        
        action_log = {
            "step": loop_count,
            "tool_name": tool_call.tool,
            "input": tool_call.arguments,
            "output": tool_response.data,
            "status": "success" if tool_response.success else "failed"
        }
        executed_actions.append(action_log)
        
        step_exec.status = "completed" if tool_response.success else "failed"
        print(f" -> Tool result: {'SUCCESS' if tool_response.success else 'FAILED'}")
        
        emit_trace_event(
            session_id, 
            exec_id, 
            "success" if tool_response.success else "failed", 
            outputs={"data": tool_response.data}, 
            error=tool_response.error, 
            latency=exec_time
        )

        if not tool_response.success:
            return ChatResponse(response=f"Failure: {tool_response.error}", response_type="error", trace=trace, session_id=session_id)
            
        current_history.append({"role": "user", "content": current_message})
        current_history.append({"role": "assistant", "content": f"Output from {tool_call.tool}: {tool_response.data}"})
        
        if tool_call.tool in mutative_tools:
             current_message = f"'{tool_call.tool}' completed. Original: '{chat_request.message}'. Wrap up now."
        else:
             current_message = f"Result of {tool_call.tool} received. Original: '{chat_request.message}'."

    return ChatResponse(response="Max steps reached.", response_type="error", trace=trace, session_id=session_id)
