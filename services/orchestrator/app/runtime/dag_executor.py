import asyncio
import time
from typing import Dict, Any, List

from app.schemas import ExecutionGraph, DAGNode, DAGNodeResult, ToolCall
from app.executor import execute_tool
from app.utils.logger import logger
from app.core.tracker import emit_trace_event

async def execute_dag(graph: ExecutionGraph, context: Dict[str, Any], session_id: str) -> ExecutionGraph:
    """
    Executes a DAG of tool calls concurrently.
    """
    logger.info(f"[DAG EXECUTOR] Starting execution of DAG with {len(graph.nodes)} nodes.")
    
    # Build adjacency lists
    # dependencies[node_id] = list of nodes that must complete before node_id
    dependencies = {n.id: [] for n in graph.nodes}
    
    for edge in graph.edges:
        if len(edge) == 2:
            src, dst = edge
            if dst in dependencies:
                dependencies[dst].append(src)
                
    # State tracking
    results: Dict[str, DAGNodeResult] = {}
    completed_events = {n.id: asyncio.Event() for n in graph.nodes}
    
    # Make sure we don't block forever if there's a cycle (which planner shouldn't emit, but just in case)
    # Actually if there's a cycle, the wait() will deadlock. In a robust system we should run a cycle check.
    
    async def execute_node(node: DAGNode):
        # Wait for all dependencies to complete
        for dep in dependencies[node.id]:
            # If the dep isn't in graph, skip waiting
            if dep in completed_events:
                await completed_events[dep].wait()
            
        logger.info(f"[DAG EXECUTOR] Running node {node.id} ({node.tool})")
        start_time = time.perf_counter()
        start_timestamp_ms = time.time() * 1000
        
        # Execute tool
        tool_call = ToolCall(tool=node.tool, arguments=node.input)
        
        # Context includes user IDs
        gmail_id = context.get("gmail_user_id")
        drive_id = context.get("drive_user_id")
        cal_id = context.get("calendar_user_id")
        
        emit_trace_event(session_id, node.id, "running", node_type="dag_node", name=node.label, inputs=node.input, meta={"tool_name": node.tool})
        
        try:
            tool_response = await execute_tool(
                tool_call,
                gmail_user_id=gmail_id,
                drive_user_id=drive_id,
                calendar_user_id=cal_id
            )
            
            end_time = time.perf_counter()
            end_timestamp_ms = time.time() * 1000
            duration_ms = (end_time - start_time) * 1000
            
            status = "success" if tool_response.success else "failed"
            
            result = DAGNodeResult(
                node_id=node.id,
                label=node.label,
                tool=node.tool,
                start_time=start_timestamp_ms,
                end_time=end_timestamp_ms,
                duration_ms=duration_ms,
                status=status,
                input=node.input,
                output=tool_response.data if tool_response.success else {"error": tool_response.error},
                error=tool_response.error if not tool_response.success else None
            )
            results[node.id] = result
            
            emit_trace_event(
                session_id, 
                node.id, 
                status, 
                outputs={"data": result.output}, 
                error=tool_response.error if not tool_response.success else None,
                latency=duration_ms,
                meta={"tool_name": node.tool}
            )
            
        except Exception as e:
            end_time = time.perf_counter()
            end_timestamp_ms = time.time() * 1000
            duration_ms = (end_time - start_time) * 1000
            
            logger.error(f"[DAG EXECUTOR] Node {node.id} failed with exception: {e}")
            result = DAGNodeResult(
                node_id=node.id,
                label=node.label,
                tool=node.tool,
                start_time=start_timestamp_ms,
                end_time=end_timestamp_ms,
                duration_ms=duration_ms,
                status="failed",
                input=node.input,
                output={"error": str(e)},
                error=str(e)
            )
            results[node.id] = result
            
            emit_trace_event(session_id, node.id, "failed", error=str(e), latency=duration_ms, meta={"tool_name": node.tool})
            
        finally:
            completed_events[node.id].set()

    # Create tasks for all nodes
    tasks = [asyncio.create_task(execute_node(n)) for n in graph.nodes]
    
    if tasks:
        # Wait for all to complete
        await asyncio.gather(*tasks)
    
    logger.info(f"[DAG EXECUTOR] Completed DAG execution.")
    
    # Update graph with results
    graph.node_results = [results[n.id] for n in graph.nodes if n.id in results]
    return graph
