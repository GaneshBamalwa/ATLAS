"""
services/orchestrator/llm/prompts.py - Centralized system prompts and helper templates
"""

import datetime
import re
from app.tool_registry import registry

# Regex patterns for fast classification of tool hints
TOOL_HINT_PATTERNS = [
    re.compile(r"\b(email|mail|gmail|inbox|message|send\s+email|reply\s+to\s+email)\b", re.IGNORECASE),
    re.compile(r"\b(calendar|meeting|event|schedule|appointment|invite)\b", re.IGNORECASE),
    re.compile(r"\b(drive|file|document|folder|share\s+link|upload|download|search\s+drive)\b", re.IGNORECASE),
    re.compile(r"\b(open|read|find|search|send|draft|delete|trash|move|share)\b", re.IGNORECASE),
]

DIRECT_ANSWER_SYSTEM_PROMPT = """You are a helpful assistant.

Answer the user's message directly in natural language.
Do not mention tools, JSON, routing, orchestration, or internal systems.
Use concise markdown formatting when helpful.
If you use headings, place heading text on its own line.
If you use lists, put each item on its own line and keep a blank line before the list.
Do not collapse multiple sections into a single line.
"""

SYSTEM_PROMPT_TEMPLATE = """You are the reasoning engine of an AI orchestration system.

Your responsibilities:
1. Understand user intent
2. Execute tool calls when necessary
3. Chain tools if needed
4. SYNTHESIZE a helpful final human response once tools are finished.

CRITICAL RULES:
1. ALWAYS use the unique 'id' returned from search results (search_drive, search_emails) when calling follow-up tools (get_drive_share_link, read_email). NEVER use 'name' or 'subject' as an ID.
2. DO NOT verify success by running another tool if the previous tool's output already confirms it.
3. If you have gathered the requested information, DO NOT use any more tools. Set 'requires_tool' to false and put the summary in 'final_result' IMMEDIATELY.
4. NEVER repeat a tool call with the same arguments.
5. Provide a warm, human-friendly summary in 'final_result'.
6. Always output valid JSON.

OUTPUT FORMAT (JSON only):
{{
  "intent": "<intent>",
  "requires_tool": true | false,
  "actions": [
    {{
      "step": 1,
      "tool_name": "<tool name>",
      "input": {{ ... }}
    }}
  ],
  "final_result": "<User-facing summary of results if tools are done, or follow-up question>",
  "confidence": 0.0 - 1.0
}}
"""

def build_system_prompt(context: dict = None) -> str:
    """Compiles the primary routing instruction with context, memory and schemas"""
    now = datetime.datetime.now()
    sys_context = f"Current Time: {now.strftime('%A, %B %d, %Y %I:%M %p')}\n"
    if context:
        sys_context += f"User Email: {context.get('email', 'N/A')}\n"
    
    memory = "None"
    if context and context.get("relevant_past_memories"):
        memory = "\n".join([str(m) for m in context.get("relevant_past_memories")])

    return f"{SYSTEM_PROMPT_TEMPLATE}\n\n### CONTEXT\n{sys_context}\n\n### TOOLS\n{registry.tool_descriptions_for_prompt()}\n\n### MEMORY\n{memory}"


def build_context_block(context: dict = None) -> str:
    """Builds short-term context metadata block"""
    now = datetime.datetime.now()
    sys_context = f"Current Time: {now.strftime('%A, %B %d, %Y %I:%M %p')}\n"
    if context:
        sys_context += f"User Email: {context.get('email', 'N/A')}\n"

    memory = "None"
    if context and context.get("relevant_past_memories"):
        memory = "\n".join([str(m) for m in context.get("relevant_past_memories")])

    return f"### CONTEXT\n{sys_context}\n### MEMORY\n{memory}"
