from typing import List, Dict, Any, Tuple
from app.schemas import DAGNode, DAGNodeMetadata
from app.tool_registry import registry
from app.utils.logger import logger

def normalize_dag(raw_nodes: List[Dict[str, Any]], raw_edges: List[Any]) -> Tuple[List[DAGNode], List[List[str]]]:
    """
    Cleans raw DAG output to ensure:
    - Pure execution units
    - No reasoning text inside nodes
    - Valid tools
    - Enforced dependencies from node definitions or explicit edge array
    """
    normalized_nodes = []
    edges = set()
    node_map = {}
    
    # Track original to new ID in case we merge or drop
    id_mapping = {}

    for i, r_node in enumerate(raw_nodes):
        node_id = r_node.get("id", f"node_{i}")
        tool_name = r_node.get("tool", "")
        
        # Rule 3: Remove invalid nodes (drop nodes that do not map to a tool or contain pure text reasoning)
        if not tool_name or not registry.get(tool_name):
            logger.warning(f"[NORMALIZER] Dropping invalid node {node_id}: tool '{tool_name}' not found.")
            continue
            
        # Extract fields securely, defaulting if missing
        label = r_node.get("label", tool_name)
        # Rule 4: Normalize labels (short verb phrases)
        if len(label.split()) > 4:
            # Quick heuristic to shorten long sentences
            label = " ".join(label.split()[:4]) + "..."
            
        # Rule 1: Split mixed nodes - enforce purely execution data
        # Strip LLM reasoning, chain of thought, etc by only copying exact fields.
        input_data = r_node.get("input", {})
        if not isinstance(input_data, dict):
            input_data = {}
            
        metadata = DAGNodeMetadata(created_by="planner", estimated_cost=0.0, priority=1)
        
        # Rule 2: Enforce explicit dependencies
        deps = r_node.get("dependencies", [])
        if not isinstance(deps, list):
            deps = []
            
        n = DAGNode(
            id=node_id,
            label=label,
            tool=tool_name,
            input=input_data,
            dependencies=deps,
            metadata=metadata
        )
        
        normalized_nodes.append(n)
        node_map[node_id] = n
        id_mapping[node_id] = node_id

    # Gather explicit edges from the raw payload
    for edge in raw_edges:
        if isinstance(edge, list) and len(edge) == 2:
            s, t = edge
            if s in node_map and t in node_map:
                edges.add((s, t))
                
    # Gather dependencies defined inside the node schema
    for n in normalized_nodes:
        for dep in n.dependencies:
            if dep in node_map:
                edges.add((dep, n.id))

    # Acyclic check (simple cycle drop)
    adj = {n.id: set() for n in normalized_nodes}
    for s, t in edges:
        adj[t].add(s) # t depends on s
        
    safe_edges = []
    # Check for cycles
    def has_cycle(start, current, visited):
        if current == start and visited: return True
        if current in visited: return False
        visited.add(current)
        for dep in adj[current]:
            if has_cycle(start, dep, visited.copy()):
                return True
        return False

    for s, t in edges:
        # Before adding, check if it creates a cycle
        if has_cycle(t, s, set()):
            logger.warning(f"[NORMALIZER] Dropping edge {s}->{t} due to cycle detection.")
        else:
            safe_edges.append([s, t])
            # For the node object itself
            if s not in node_map[t].dependencies:
                node_map[t].dependencies.append(s)

    return normalized_nodes, safe_edges
