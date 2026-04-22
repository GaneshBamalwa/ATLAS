import httpx
import json
from app.config import get_settings
from app.utils.logger import logger, log_execution_time
from dotenv import dotenv_values

settings = get_settings()

GROQ_SYSTEM_PROMPT = """You are a professional AI response generator.

Your task is to synthesize a final human-readable response based on the structured data provided. The 'final_result' field contains the core answer from the reasoning engine.

RULES:
- Use 'final_result' as your primary source of truth.
- Use 'actions' strictly to fill in any missing specific details (e.g., exact names, IDs, or links) that 'final_result' may have omitted.
- Do NOT invent information. Do NOT hallucinate.
- NEVER mention tools, internal systems, JSON, or the reasoning engine.
- Produce a natural, polished, and direct response to the user.
- Use markdown formatting (bolding, lists) to make it highly readable.

Return ONLY the final response string. Do not include introductory filler.
"""

@log_execution_time
async def format_response(orchestrator_output: dict) -> str:
    """Pass the orchestrator's structured JSON output to Groq for natural language formatting."""
    env_data = dotenv_values(".env")
    
    # Fast Groq layer for text synthesis over OpenRouter
    api_key = env_data.get("GROQ_API_KEY", "").strip() or env_data.get("OPENROUTER_API_KEY", "").strip()
    
    # We prefer groq models for this since it requires no reasoning, just fast text gen.
    # Llama 3.1 8B is perfect.
    model = "llama-3.1-8b-instant" 
    base_url = "https://api.groq.com/openai/v1"
    
    # Fallback to general settings if we only have OpenRouter
    if not env_data.get("GROQ_API_KEY") and env_data.get("OPENROUTER_API_KEY"):
        model = env_data.get("LLM_MODEL", settings.llm_model)
        base_url = env_data.get("LLM_BASE_URL", settings.llm_base_url)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "ATLAS Orchestrator",
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": GROQ_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(orchestrator_output, indent=2)}
        ],
        "temperature": 0.3,
        "max_tokens": 1000,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            
            if resp.status_code != 200:
                logger.error(f"[FORMATTER] Failed. Code {resp.status_code}: {resp.text}")
                return orchestrator_output.get("final_result", "I processed your request, but there was an error generating the final text.")
            
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
            
    except Exception as e:
        logger.error(f"[FORMATTER] Critical failure: {e}")
        return orchestrator_output.get("final_result", "I completed the tasks but failed to format the response.")
