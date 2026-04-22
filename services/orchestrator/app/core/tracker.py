import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from app.core.schemas_trace import ExecutionTrace, TraceNode

# In-memory store for traces.
_trace_store: Dict[str, ExecutionTrace] = {}

def get_trace(execution_id: str) -> Optional[ExecutionTrace]:
    return _trace_store.get(execution_id)

def init_trace(execution_id: str) -> ExecutionTrace:
    if execution_id not in _trace_store:
        _trace_store[execution_id] = ExecutionTrace(execution_id=execution_id, status="running")
    return _trace_store[execution_id]

def emit_trace_event(
    execution_id: str, 
    node_id: str, 
    status: str, 
    node_type: str = "unknown",
    name: str = "Unknown Node",
    inputs: Optional[Dict[str, Any]] = None, 
    outputs: Optional[Dict[str, Any]] = None, 
    meta: Optional[Dict[str, Any]] = None,
    latency: float = 0.0, 
    error: Optional[str] = None
):
    from app.utils.logger import logger
    log_msg = f"[TRACKER] Event: {node_id} ({status}) for {execution_id}"
    logger.info(log_msg)
    
    # Debug file logging
    try:
        with open("g:\\MCPs\\fresh\\services\\orchestrator\\tracker_debug.log", "a") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] {log_msg}\n")
    except Exception as e:
        logger.error(f"[TRACKER] Failed to write debug log: {e}")
        
    trace = init_trace(execution_id)
    
    existing_node = next((n for n in trace.nodes if n.id == node_id), None)
            
    if existing_node:
        existing_node.status = status
        if outputs is not None: existing_node.outputs = outputs
        if meta is not None: existing_node.meta.update(meta)
        if error is not None: existing_node.error = error
        if latency > 0:
            existing_node.latency_ms = latency
            trace.total_latency_ms += latency
            existing_node.completed_at = datetime.now(timezone.utc)
    else:
        new_node = TraceNode(
            id=node_id,
            name=name,
            type=node_type,
            status=status,
            inputs=inputs or {},
            outputs=outputs,
            meta=meta or {},
            latency_ms=latency,
            error=error
        )
        if status in ["success", "failed"]:
            new_node.completed_at = datetime.now(timezone.utc)
        trace.nodes.append(new_node)
        
    # Update global trace status
    has_failed = any(n.status == "failed" for n in trace.nodes)
    has_running = any(n.status == "running" for n in trace.nodes)
    if has_failed:
        trace.status = "failed"
    elif not has_running and status in ["success", "failed"]:
        trace.status = "success"

def get_graph_data(execution_id: str) -> Dict[str, Any]:
    """Convert ExecutionTrace into ReactFlow nodes/edges."""
    from app.utils.logger import logger
    
    log_msg = f"[TRACKER] Graph requested for: {execution_id}"
    logger.info(log_msg)
    try:
        with open("g:\\MCPs\\fresh\\services\\orchestrator\\tracker_debug.log", "a") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] {log_msg}\n")
    except: pass

    trace = get_trace(execution_id)
    if not trace: 
        warn_msg = f"[TRACKER] Graph requested for missing ID: {execution_id}"
        logger.warning(warn_msg)
        try:
            with open("g:\\MCPs\\fresh\\services\\orchestrator\\tracker_debug.log", "a") as f:
                f.write(f"[{datetime.now(timezone.utc).isoformat()}] {warn_msg}\n")
        except: pass
        return {"nodes": [], "edges": []}
    
    logger.info(f"[TRACKER] Serving graph for {execution_id} with {len(trace.nodes)} nodes")
    
    rf_nodes = []
    rf_edges = []
    
    for i, node in enumerate(trace.nodes):
        # Staggered layout: Planners on the left (x: 50), Tools on the right (x: 450)
        is_tool = node.type == "mcp_tool"
        x_pos = 450 if is_tool else 50
        
        rf_nodes.append({
            "id": node.id,
            "type": "customNode",
            "position": {"x": x_pos, "y": i * 180},
            "data": {
                "label": f"{node.name}: {node.type}",
                "node_name": node.name,
                "node_type": node.type,
                "status": node.status,
                "summary": node.error or (f"Latency: {node.latency_ms:.1f}ms" if node.latency_ms else ""),
                "latency_ms": node.latency_ms,
                "inputs": node.inputs,
                "outputs": node.outputs,
                "meta": node.meta,
                "error": node.error
            }
        })
        
        if i > 0:
            rf_edges.append({
                "id": f"e-{trace.nodes[i-1].id}-{node.id}",
                "source": trace.nodes[i-1].id,
                "target": node.id,
                "animated": node.status == "running"
            })
            
    return {"nodes": rf_nodes, "edges": rf_edges}

def get_timeline_data(execution_id: str) -> List[Dict[str, Any]]:
    """Convert trace into chronological events."""
    trace = get_trace(execution_id)
    if not trace: return []
    
    events = []
    for node in trace.nodes:
        events.append({
            "timestamp": node.started_at.isoformat(),
            "type": "node_started",
            "message": f"Started {node.name}",
            "node_id": node.id
        })
        if node.completed_at:
            events.append({
                "timestamp": node.completed_at.isoformat(),
                "type": "node_finished",
                "message": f"Finished {node.name} with status {node.status}",
                "status": node.status,
                "node_id": node.id
            })
    return sorted(events, key=lambda x: x["timestamp"])

def list_recent_traces(limit: int = 10) -> List[Dict[str, Any]]:
    """List recent traces with minimal metadata."""
    results = []
    # Sort by recent (assuming newer traces are added later to the dict keys or we use start time)
    # Since it's a dict, we'll just take the last N or sort by node count as a proxy for activity
    # Actually, let's sort by started_at if we can.
    
    for eid, trace in _trace_store.items():
        results.append({
            "execution_id": eid,
            "status": trace.status,
            "node_count": len(trace.nodes),
            "timestamp": trace.started_at.isoformat() if hasattr(trace, 'started_at') and trace.started_at else datetime.now(timezone.utc).isoformat()
        })
    
    # Sort by timestamp descending
    results.sort(key=lambda x: x["timestamp"], reverse=True)
    return results[:limit]
