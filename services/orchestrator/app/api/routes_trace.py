from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.core.tracker import get_trace
import uuid
import time
from pydantic import BaseModel

router = APIRouter(prefix="/trace", tags=["Observability"])

@router.get("/{execution_id}")
async def get_execution_trace(execution_id: str):
    """Retrieve the full JSON trace of a specific execution ID."""
    trace = get_trace(execution_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found or expired")
    return trace.dict()

@router.get("/{execution_id}/graph")
async def get_react_flow_graph(execution_id: str):
    """Return execution trace mapped to a React Flow compatible format."""
    trace = get_trace(execution_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
        
    nodes = []
    edges = []
    
    # Map nodes
    for idx, node in enumerate(trace.nodes):
        
        # Visually logical staggering based on agent type
        x_pos = 250
        summary = "Processing node"
        
        if "llm_planner" in node.type.lower() or "planner" in node.type.lower():
            x_pos = 250
            if idx == 0:
                summary = "Analyzing user intent and planning workflow"
            else:
                summary = "Evaluating tool output and reasoning next step"
        elif "mcp_tool" in node.type.lower() or "tool" in node.type.lower():
            x_pos = 550
            tool_name = node.inputs.get("tool", "unknown_action").replace("_", " ")
            summary = f"Executing action: {tool_name.title()}"
        elif "formatter" in node.type.lower() or "format" in node.type.lower():
            x_pos = 250
            summary = "Synthesizing structured conversation response"
            
        nodes.append({
            "id": node.id,
            "type": "customNode",
            "data": {
                "label": node.name if node.name != "Unknown Node" else node.type.upper(),
                "node_name": node.name,
                "node_type": node.type,
                "summary": summary,
                "status": node.status,
                "latency_ms": node.latency_ms,
                "inputs": node.inputs,
                "outputs": node.outputs,
                "meta": node.meta,
                "error": node.error,
                "started_at": node.started_at.isoformat() if node.started_at else None,
                "completed_at": node.completed_at.isoformat() if node.completed_at else None
            },
            "position": {"x": x_pos, "y": 150 * idx + 50}
        })
        
        # Sequentially link to the next node if it exists
        if idx < len(trace.nodes) - 1:
            next_node = trace.nodes[idx+1]
            edges.append({
                "id": f"edge_{node.id}_{next_node.id}",
                "source": node.id,
                "target": next_node.id,
                "animated": True,
                "type": "smoothstep",
                "style": {"stroke": "#10b981" if next_node.status == "success" else "#8b5cf6", "strokeWidth": 2.5}
            })
            
    return {
        "nodes": nodes,
        "edges": edges
    }

@router.get("/{execution_id}/timeline")
async def get_execution_timeline(execution_id: str):
    """Retrieve chronologically ordered events for the execution."""
    trace = get_trace(execution_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    
    events = []
    for node in trace.nodes:
        events.append({
            "timestamp": node.started_at,
            "type": "node_started",
            "node_id": node.id,
            "node_name": node.name,
            "message": f"Started {node.name}"
        })
        if node.completed_at:
            events.append({
                "timestamp": node.completed_at,
                "type": "node_completed",
                "node_id": node.id,
                "node_name": node.name,
                "status": node.status,
                "message": f"Completed {node.name} with status {node.status}"
            })
            
    events.sort(key=lambda x: x["timestamp"])
    return events

class FailureSimulationRequest(BaseModel):
    node_id: str
    fault_type: str = "error" # timeout, error, invalid_response

# Global simulation registry
SIMULATED_FAILURES: Dict[str, Dict[str, str]] = {}

@router.post("/{execution_id}/simulate_failure")
async def simulate_failure(execution_id: str, req: FailureSimulationRequest):
    """Inject a failure into a future node execution."""
    if execution_id not in SIMULATED_FAILURES:
        SIMULATED_FAILURES[execution_id] = {}
    
    SIMULATED_FAILURES[execution_id][req.node_id] = req.fault_type
    return {"status": "configured", "node_id": req.node_id, "fault_type": req.fault_type}

@router.post("/{execution_id}/replay")
async def replay_execution(execution_id: str):
    """Kicks off a replay of the execution based on its trace."""
    trace = get_trace(execution_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    
    # In a real system, we would re-invoke the orchestrator with the original user message
    # For now we'll return a simulated acknowledgment
    new_exe_id = f"replay_{uuid.uuid4().hex[:8]}"
    return {
        "original_execution_id": execution_id,
        "new_execution_id": new_exe_id,
        "message": "Replay initiated successfully (Simulation)"
    }

