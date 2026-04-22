import os
import json
import logging
from groq import Groq
from openai import OpenAI
from backend.config import settings

logger = logging.getLogger(__name__)

def get_groq_client():
    if not settings.GROQ_API_KEY: return None
    return Groq(api_key=settings.GROQ_API_KEY, timeout=90.0)

def get_openrouter_client():
    if not settings.OPENROUTER_API_KEY: return None
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
        timeout=120.0
    )

def _execute_llm(prompt: str, json_mode: bool = False, fallback=""):
    # 1. Try OpenRouter (Primary as per user request)
    or_client = get_openrouter_client()
    if or_client:
        kwargs = {
            "model": settings.ALTERNATE_MODEL, # e.g. "meta-llama/llama-3.1-8b-instruct"
            "extra_headers": {
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Gmail MCP",
            },
            "messages": [{"role": "user", "content": prompt}]
        }
        if json_mode:
            # Explicitly force JSON via system prompt for OpenRouter
            kwargs["messages"].insert(0, {"role": "system", "content": "You MUST return ONLY a valid JSON object."})
            
        try:
            response = or_client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenRouter failed: {e}. Falling back to Groq...")

    # 2. Try Groq (Fallback)
    g_client = get_groq_client()
    if g_client:
        kwargs = {
            "model": settings.LLM_MODEL,
            "temperature": settings.LLM_TEMPERATURE,
            "messages": [{"role": "user", "content": prompt}]
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
            kwargs["messages"].insert(0, {"role": "system", "content": "You are a helpful assistant that outputs ONLY valid JSON."})
        
        try:
            response = g_client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq also failed: {e}")
            
    return fallback

def summarize_email(content: str) -> str:
    if not content: return ""
    # Truncate content to avoid TPM limits (approx 8000 tokens)
    safe_content = content[:15000] 
    prompt = f"Please summarize the following email content concisely (max 2-3 sentences):\n\n{safe_content}"
    return _execute_llm(prompt, fallback="Summarization unavailable.")

def draft_email_response(original_email: str, instructions: str) -> str:
    safe_email = original_email[:10000]
    prompt = f"Draft an email reply to the following email:\n{safe_email}\n\nInstructions: {instructions}"
    return _execute_llm(prompt, fallback="Failed to draft email.")

def draft_new_email(topic: str) -> str:
    prompt = f"Write a clear, professional email about the following instructions. Return ONLY the email body. \n\nInstructions: {topic}"
    return _execute_llm(prompt, fallback="Failed to draft email.")

def generate_search_query(natural_language: str) -> str:
    prompt = f"Convert this text into a Gmail search query. Return ONLY the search query text.\n\nText: {natural_language}"
    return _execute_llm(prompt, fallback=natural_language)

def generate_subject_line(content: str) -> str:
    if not content.strip(): return "No Subject"
    safe_content = content[:5000]
    prompt = f"Based on the following email content, generate a very concise, professional subject line. Return ONLY the text.\n\nContent:\n{safe_content}"
    subj = _execute_llm(prompt, fallback="No Subject")
    return subj.replace('Subject: ', '').replace('"', '')

def batch_summarize_emails(emails: list) -> dict:
    """Processes multiple emails in a single LLM call to bypass per-request rate limits."""
    if not emails: return {}
    if not settings.ENABLE_EMAIL_INTELLIGENCE: return {}
    
    # Bundle emails into a structured prompt
    bundle = []
    for i, e in enumerate(emails):
        # Truncate content to keep total prompt size safe
        content = e.get("body", "")[:3000]
        bundle.append(f"--- EMAIL {i} ---\nSubject: {e.get('subject')}\nFrom: {e.get('from')}\nContent: {content}")
        
    prompt = f"""
    Analyze these {len(emails)} emails. For each, provide a JSON entry with:
    'summary': concise 1-sentence summary
    'classification': urgent|promo|spam|personal|work
    'intent': action_required|informational|meeting|follow_up
    
    Return a JSON object where keys are "email_0", "email_1", etc. matching the order below.
    
    Emails:
    {chr(10).join(bundle)}
    """
    
    result = _execute_llm(prompt, json_mode=True, fallback="{}")
    try:
        data = json.loads(result)
        return data if isinstance(data, dict) else {}
    except:
        return {}

def enrich_email(content: str, subject: str = "", sender: str = "") -> dict:
    if not settings.ENABLE_EMAIL_INTELLIGENCE:
        return {}
        
    safe_content = content[:10000]
    prompt = f"""
    Analyze the following email and return a JSON object with this exact structure:
    {{
        "classification": "urgent|promo|spam|personal|work",
        "intent": "action_required|informational|meeting|follow_up",
        "priority": "high|medium|low",
        "entities": {{
            "dates": ["list of strings"],
            "people": ["list of strings"],
            "actions": ["list of strings"]
        }}
    }}
    Email Subject: {subject}
    Email Content: {safe_content}
    """
    
    result = _execute_llm(prompt, json_mode=True, fallback="{}")
    try:
        data = json.loads(result)
        return data if isinstance(data, dict) else {}
    except:
        return {}
def suggest_alternate_slots(event_summary: str, conflicts: list) -> str:
    """Analyze conflicts and suggest 2 alternative time slots."""
    if not conflicts: return ""
    
    conflict_text = "\n".join([f"- {c['summary']} at {c['start']}" for c in conflicts])
    prompt = f"""
    The user wants to schedule: '{event_summary}'.
    However, there are conflicts:
    {conflict_text}
    
    Suggest 2 alternative date/time slots on the same day that are free.
    Return a concise, human-friendly list of suggestions.
    Time Zone is Asia/Kolkata (IST).
    """
    return _execute_llm(prompt, fallback="Unable to suggest alternatives.")
