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
    """Convert ExecutionTrace into ReactFlow nodes/edges forming a proper DAG."""
    import json
    import re
    from app.utils.logger import logger
    
    log_msg = f"[TRACKER] Graph requested for: {execution_id}"
    logger.info(log_msg)

    trace = get_trace(execution_id)
    if not trace: 
        logger.warning(f"[TRACKER] Graph requested for missing ID: {execution_id}")
        return {"nodes": [], "edges": []}
    
    logger.info(f"[TRACKER] Serving graph for {execution_id} with {len(trace.nodes)} nodes")
    
    # Separate nodes by type
    planner_node = next((n for n in trace.nodes if n.type == "planner"), None)
    synth_node = next((n for n in trace.nodes if n.type == "synthesis"), None)
    tool_nodes = [n for n in trace.nodes if n.type == "mcp_tool" or n.type == "dag_node"]
    
    dependencies = {n.id: [] for n in tool_nodes}
    is_dependency_of = {n.id: [] for n in tool_nodes}
    tool_name_to_id = {n.name: n.id for n in tool_nodes}
    
    # Extract dependencies based on {tool_name.property} in inputs
    for n in tool_nodes:
        original = n.meta.get("original_params", n.inputs) if n.meta else n.inputs
        if not original: continue
        params_str = json.dumps(original, default=str)
        refs = re.findall(r'\{([A-Za-z0-9_]+)\.', params_str)
        for ref in refs:
            if ref in tool_name_to_id and tool_name_to_id[ref] != n.id:
                dep_id = tool_name_to_id[ref]
                if dep_id not in dependencies[n.id]:
                    dependencies[n.id].append(dep_id)
                    is_dependency_of[dep_id].append(n.id)

    # Calculate depth for layout
    depths = {n.id: 0 for n in tool_nodes}
    changed = True
    while changed:
        changed = False
        for n in tool_nodes:
            for dep_id in dependencies[n.id]:
                if depths[n.id] < depths[dep_id] + 1:
                    depths[n.id] = depths[dep_id] + 1
                    changed = True

    # Group tools by depth to stagger X positions for parallel execution
    nodes_by_depth = {}
    for n in tool_nodes:
        d = depths[n.id]
        if d not in nodes_by_depth:
            nodes_by_depth[d] = []
        nodes_by_depth[d].append(n)

    rf_nodes = []
    rf_edges = []
    
    # 1. Add Planner Node
    if planner_node:
        rf_nodes.append({
            "id": planner_node.id,
            "type": "customNode",
            "position": {"x": 400, "y": 50},
            "data": {
                "label": planner_node.name,
                "node_name": planner_node.name,
                "node_type": planner_node.type,
                "status": planner_node.status,
                "summary": planner_node.error or (f"Latency: {planner_node.latency_ms:.1f}ms" if planner_node.latency_ms else ""),
                "latency_ms": planner_node.latency_ms,
                "inputs": planner_node.inputs,
                "outputs": planner_node.outputs,
                "meta": planner_node.meta,
                "error": planner_node.error,
                "start_time": planner_node.started_at.isoformat(),
                "end_time": planner_node.completed_at.isoformat() if planner_node.completed_at else None,
            }
        })
        
        # Connect Planner to Root Tools
        if tool_nodes:
            for n in tool_nodes:
                if not dependencies[n.id]:
                    rf_edges.append({
                        "id": f"e-{planner_node.id}-{n.id}",
                        "source": planner_node.id,
                        "target": n.id,
                        "animated": n.status == "running"
                    })
        elif synth_node:
            rf_edges.append({
                "id": f"e-{planner_node.id}-{synth_node.id}",
                "source": planner_node.id,
                "target": synth_node.id,
                "animated": synth_node.status == "running"
            })

    # 2. Add Tool Nodes & Internal Edges
    for d, level_nodes in nodes_by_depth.items():
        count = len(level_nodes)
        start_x = 400 - ((count - 1) * 150) # Center them around x=400
        for i, n in enumerate(level_nodes):
            x_pos = start_x + (i * 300)
            y_pos = 200 + (d * 180)
            
            rf_nodes.append({
                "id": n.id,
                "type": "customNode",
                "position": {"x": x_pos, "y": y_pos},
                "data": {
                    "label": n.name,
                    "node_name": n.name,
                    "node_type": n.type,
                    "status": n.status,
                    "summary": n.error or (f"Latency: {n.latency_ms:.1f}ms" if n.latency_ms else ""),
                    "latency_ms": n.latency_ms,
                    "inputs": n.inputs,
                    "outputs": n.outputs,
                    "meta": n.meta,
                    "error": n.error,
                    "start_time": n.started_at.isoformat(),
                    "end_time": n.completed_at.isoformat() if n.completed_at else None,
                }
            })
            
            for dep_id in dependencies[n.id]:
                rf_edges.append({
                    "id": f"e-{dep_id}-{n.id}",
                    "source": dep_id,
                    "target": n.id,
                    "animated": n.status == "running"
                })

    # 3. Add Synthesis Node
    if synth_node:
        max_depth = max(depths.values()) if depths else -1
        synth_y = 200 + ((max_depth + 1) * 180)
        rf_nodes.append({
            "id": synth_node.id,
            "type": "customNode",
            "position": {"x": 400, "y": synth_y},
            "data": {
                "label": synth_node.name,
                "node_name": synth_node.name,
                "node_type": synth_node.type,
                "status": synth_node.status,
                "summary": synth_node.error or (f"Latency: {synth_node.latency_ms:.1f}ms" if synth_node.latency_ms else ""),
                "latency_ms": synth_node.latency_ms,
                "inputs": synth_node.inputs,
                "outputs": synth_node.outputs,
                "meta": synth_node.meta,
                "error": synth_node.error,
                "start_time": synth_node.started_at.isoformat(),
                "end_time": synth_node.completed_at.isoformat() if synth_node.completed_at else None,
            }
        })
        
        for n in tool_nodes:
            if not is_dependency_of[n.id]:
                rf_edges.append({
                    "id": f"e-{n.id}-{synth_node.id}",
                    "source": n.id,
                    "target": synth_node.id,
                    "animated": synth_node.status == "running"
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
