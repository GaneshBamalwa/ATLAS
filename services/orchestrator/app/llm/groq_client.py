from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from openai import AsyncOpenAI

from app.core.tools import TOOL_REGISTRY
from app.utils.logger import logger


class GroqRouter:
    """OpenAI-compatible client for Groq/OpenRouter planning and synthesis."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = (api_key or os.getenv("GROQ_API_KEY") or os.getenv("OPENROUTER_API_KEY") or "").strip()
        self.model = model or os.getenv("LLM_MODEL") or "llama-3.1-70b-versatile"
        self.base_url = (
            base_url
            or os.getenv("GROQ_API_URL")
            or os.getenv("OPENROUTER_API_URL")
            or ("https://openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") else "https://api.groq.com/openai/v1")
        ).rstrip("/")
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, timeout=timeout) if self.api_key else None

    def _tool_registry_text(self, tool_registry: Optional[Dict[str, Dict[str, Any]]] = None) -> str:
        registry = tool_registry or TOOL_REGISTRY
        lines: List[str] = []
        for tool_name, meta in registry.items():
            params = ", ".join(meta.get("params", [])) or "none"
            lines.append(f"- {tool_name}: {meta.get('description', '')} | params: {params}")
        return "\n".join(lines)

    async def _chat_text(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1200,
    ) -> str:
        if not self.api_key:
            raise ValueError("Groq/OpenRouter API key is missing.")
        if self.client is None:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        return content.strip()

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        text = text.strip()
        if text.startswith("{"):
            return json.loads(text)
        if "```json" in text:
            chunk = text.split("```json", 1)[1].split("```", 1)[0]
            return json.loads(chunk)
        if "```" in text:
            chunk = text.split("```", 1)[1].split("```", 1)[0]
            return json.loads(chunk)
        return json.loads(text)

    async def plan_tools(self, query: str, tool_registry: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        tools_text = self._tool_registry_text(tool_registry)
        now = datetime.now()
        current_time = now.strftime("%A, %B %d, %Y %I:%M %p")
        today_iso = now.strftime("%Y-%m-%d")
        from datetime import timedelta
        tomorrow_iso = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        system_prompt = (
            f"You are ATLAS, an orchestration planner. The current date and time is {current_time}. "
            "Analyze the user query and return ONLY valid JSON. "
            "Do not include markdown, explanations, or code fences. "
            "Return the smallest useful set of tools. "
            "If no tools are needed, return an empty tools array.\n\n"
            f"Available tools:\n{tools_text}\n\n"
            "When one tool depends on the result of another, use placeholder strings in the dependent tool params. "
            "Use the exact syntax {tool_name.field} or {tool_name.array[0].field}. "
            "Only reference fields that come from a previous tool result, and do not invent tool names or output fields. "
            "Tools without placeholders can run in parallel. Tools with placeholders must run after the tools they reference.\n\n"
            "Example pattern:\n"
            "{\n"
            "  \"tools\": [\n"
            "    {\"name\": \"search_drive\", \"params\": {\"query\": \"hack2skill\"}},\n"
            "    {\"name\": \"get_drive_share_link\", \"params\": {\"file_id\": \"{search_drive.files[0].id}\"}},\n"
            "    {\"name\": \"send_email\", \"params\": {\"to\": \"ganeshbamalwa89@gmail.com\", \"subject\": \"Document: hack2skill\", \"body\": \"Link: {get_drive_share_link.share_link}\"}}\n"
            "  ],\n"
            "  \"reasoning\": \"Search for the file, get its link, then email the link\"\n"
            "}\n\n"
            "Rules:\n"
            "1. Use exact tool names from the registry.\n"
            "2. Use placeholders only when a tool needs output from a previous tool.\n"
            "3. Independent tools should be listed without placeholders so they can run in parallel.\n"
            "4. Never invent tools, fields, or IDs.\n"
            "5. Always include a short reasoning string.\n"
            "6. Return JSON only.\n\n"
            "DATE/TIME RULES — MANDATORY, always follow these when building tool params:\n"
            f"  - Today's date is {today_iso} and tomorrow's date is {tomorrow_iso}.\n"
            "  - ALWAYS resolve relative date words to absolute YYYY-MM-DD dates.\n"
            f"    'today' or 'tonight' -> '{today_iso}'\n"
            f"    'tomorrow' -> '{tomorrow_iso}'\n"
            "    'next Monday' etc -> compute the actual calendar date as YYYY-MM-DD\n"
            "  - ALWAYS convert 12-hour time expressions to 24-hour HH:MM for tool params.\n"
            "    '6 pm' -> '18:00'  |  '6:00 PM' -> '18:00'  |  '9 am' -> '09:00'\n"
            "    '12 noon' -> '12:00'  |  '12 midnight' -> '00:00'  |  '6:30 pm' -> '18:30'\n"
            "  - For add_calendar_event: 'date' MUST be YYYY-MM-DD, 'start_time' MUST be HH:MM (24-hour).\n"
            "  - NEVER pass relative strings like 'tomorrow', '6 pm', 'next week' as tool param values.\n\n"
            '{"tools":[{"name":"tool_name","params":{}}],"reasoning":"why these tools"}'
        )
        user_prompt = f"User query: {query}"
        response_text = await self._chat_text(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=1200,
        )

        logger.info("[GROQ] Tool plan raw response: %s", response_text)
        result = self._extract_json(response_text)
        result.setdefault("tools", [])
        result.setdefault("reasoning", "")
        return result

    async def synthesize_response(
        self,
        original_query: str,
        tool_results: Dict[str, Any],
        reasoning: str,
    ) -> str:
        if not tool_results or all(not value for value in tool_results.values()):
            lowered_query = original_query.lower()
            if "drive profile" in lowered_query or "google drive profile" in lowered_query:
                return "Google Drive profile information is not available through the current Drive tools. I can search, read, trash, or share files instead."
            if "gmail profile" in lowered_query or "email profile" in lowered_query:
                return "Gmail profile information is not available through the current tools. I can search your inbox, read messages, or list unread emails instead."
            return "I couldn't find a direct tool result for that request. Try a more specific Google Drive, Gmail, or Calendar action."

        results_str = json.dumps(tool_results, indent=2, ensure_ascii=False, default=str)
        system_prompt = (
            "You are an AI assistant that synthesizes tool results into concise, readable responses.\n\n"
            "FORMATTING RULES:\n"
            "1. Be direct and brief\n"
            "2. Use markdown only when it improves readability\n"
            "3. For lists, use simple numbered items with one short line each\n"
            "4. Avoid large headings unless the user explicitly asks for a report\n"
            "5. Do not add verbose introductions, summaries, or filler\n"
            "6. If the result is an error or empty, say that plainly in one or two sentences\n"
        )
        user_prompt = (
            f"Original query: {original_query}\n"
            f"Reasoning: {reasoning}\n"
            f"Tool results:\n{results_str}\n\n"
            "Return a concise answer. Use markdown only if it keeps the response easy to scan."
        )
        return await self._chat_text(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1500,
        )

    async def classify_intent(self, query: str) -> Dict[str, Any]:
        return await self.plan_tools(query=query)

    async def stream_response(self, prompt: str):
        # Keep a compatibility shim for older callers.
        text = await self._chat_text([{"role": "user", "content": prompt}], temperature=0.2, max_tokens=1200)
        yield text

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            if self.client is None:
                self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            await self.client.models.list()
            return True
        except Exception as exc:
            logger.warning("[GROQ] health check failed: %s", exc)
            return False
