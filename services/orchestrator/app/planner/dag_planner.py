import json
import re
import httpx
from typing import Optional, Dict, Any, List
from dotenv import dotenv_values

from app.config import get_settings
from app.tool_registry import registry
from app.utils.logger import logger
from app.schemas import ExecutionGraph, DAGNode

settings = get_settings()

DAG_PLANNER_SYSTEM_PROMPT = """You are the DAG (Directed Acyclic Graph) Planner of an AI orchestration system.

Your job is to take the user's query and generate a strict JSON execution DAG. 
Each node represents a tool execution. Nodes can run in parallel if they have no dependencies on each other.

### REQUIRED FORMAT (STRICT JSON ONLY)
{
  "nodes": [
    {
      "id": "n1",
      "label": "Search Drive",
      "tool": "drive.search",
      "input": { "query": "proposal" },
      "dependencies": [],
      "metadata": {
        "created_by": "planner",
        "estimated_cost": 0,
        "priority": 1
      }
    },
    {
      "id": "n2",
      "label": "Check Calendar",
      "tool": "calendar.check",
      "input": { "range": "next week" },
      "dependencies": [],
      "metadata": {
        "created_by": "planner",
        "estimated_cost": 0,
        "priority": 1
      }
    },
    {
      "id": "n3",
      "label": "Send Email",
      "tool": "gmail.send",
      "input": { "to": "user@example.com" },
      "dependencies": ["n1", "n2"],
      "metadata": {
        "created_by": "planner",
        "estimated_cost": 0,
        "priority": 1
      }
    }
  ],
  "edges": []
}

### RULES
1. "nodes" must be a list of executable tasks following the strict schema above.
2. DO NOT include ANY reasoning text, logs, or intermediate outputs inside the nodes. PURE EXECUTION ONLY.
3. Use the "dependencies" array inside the node to list IDs of nodes that must complete first.
4. The graph MUST be acyclic.
5. If there are no tool calls needed, output an empty nodes list.
6. Provide a clean, short human-readable "label" (e.g. "Search Drive"). No full sentences.
7. The "tool" field must exactly match one of the available tool names.
8. Return ONLY valid JSON, nothing else. No markdown wrapping.
"""

def _extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    bare = re.search(r"(\{.*\})", text, re.DOTALL)
    if bare:
        try:
            return json.loads(bare.group(1))
        except:
            pass
    return None

async def plan_dag(user_query: str, history: List[Dict[str, str]] = None, context: Dict[str, Any] = None) -> ExecutionGraph:
    logger.info("[DAG PLANNER] Generating execution DAG...")
    
    # Build prompt
    tools_str = registry.tool_descriptions_for_prompt()
    system_content = f"{DAG_PLANNER_SYSTEM_PROMPT}\n\n### AVAILABLE TOOLS\n{tools_str}"
    if context:
        system_content += f"\n\n### CONTEXT\n{json.dumps(context)}"
        
    messages = [{"role": "system", "content": system_content}]
    if history:
        messages.extend(history[-4:])
    messages.append({"role": "user", "content": user_query})
    
    env = dotenv_values(".env")
    api_key = env.get("OPENROUTER_API_KEY", "").strip() or env.get("GROQ_API_KEY", "").strip()
    
    # Fast planning model
    model = "llama-3.1-8b-instant"
    base_url = "https://api.groq.com/openai/v1"
    
    if not env.get("GROQ_API_KEY"):
        model = env.get("LLM_MODEL", settings.llm_model)
        base_url = env.get("LLM_BASE_URL", settings.llm_base_url)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "max_tokens": 1000,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{base_url}/chat/completions", json=payload, headers={"Authorization": f"Bearer {api_key}"})
            if resp.status_code != 200:
                raise Exception(f"API Error {resp.status_code}")
                
            raw = resp.json()["choices"][0]["message"].get("content") or ""
            parsed = _extract_json(raw)
            if not parsed and raw:
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = {}
            if not parsed:
                parsed = {}
            
            raw_nodes = parsed.get("nodes", [])
            raw_edges = parsed.get("edges", [])
            
            from app.runtime.dag_normalizer import normalize_dag
            nodes, edges = normalize_dag(raw_nodes, raw_edges)
            
            return ExecutionGraph(nodes=nodes, edges=edges)
            
    except Exception as e:
        logger.error(f"[DAG PLANNER] Failed to plan DAG: {e}")
        return ExecutionGraph()
