"""
LLM Agent — Communicates with Ollama (llama3.1:8b) for intent detection,
entity extraction, and response generation.
"""

import json
import httpx

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.1:8b"


SYSTEM_PROMPT = """You are Senate Bot, an AI governance assistant for Indian citizens.
Your job is to help citizens interact with government services through natural conversation.

You can perform the following actions by outputting a JSON tool-call block:

1. **check_ration** — Look up a ration card status.
   Required entity: ration_id (format: two uppercase letters + six digits, e.g., MH123456)

2. **check_birth** — Look up a birth certificate status.
   Required entity: certificate_id (format: BC followed by digits, e.g., BC1021)

3. **check_location** — Look up location info from a PIN code.
   Required entity: pin (6-digit Indian PIN code, e.g., 400001)

4. **register_grievance** — Register a public grievance.
   Required entities: name, description.  Optional: category, pin.

5. **check_eligibility** — Check eligibility for a government scheme.
   Ask follow-up questions to gather: income, age, category (SC/ST/OBC/General), state, family_size.

RULES:
- If you can identify the user's intent AND have the required entities, respond ONLY with a JSON block like:
  {"action": "<action_name>", "entities": {<key>: <value>, ...}}
- If you need more information from the user, ask a clear follow-up question in plain text — do NOT output JSON.
- Always be polite, concise, and helpful.
- When you cannot help, suggest that the user be escalated to a human officer.
- Do NOT invent data. Only trigger tool calls with entities explicitly provided by the user.
"""


async def query_llm(conversation: list[dict]) -> str:
    """
    Send the conversation history to Ollama and return the assistant's reply.
    `conversation` is a list of {"role": "user"|"assistant"|"system", "content": "..."}
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.3,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(OLLAMA_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
    except httpx.ConnectError:
        return (
            "⚠️ I'm unable to reach the language model server (Ollama). "
            "Please make sure Ollama is running with `ollama serve` and the "
            "llama3.1:8b model is pulled."
        )
    except Exception as e:
        return f"⚠️ An error occurred while processing your request: {str(e)}"


def parse_action(llm_response: str) -> dict | None:
    """
    Try to extract a JSON action block from the LLM response.
    Returns the parsed dict if found, else None.
    """
    # Try to find JSON in the response
    text = llm_response.strip()

    # If the whole response is JSON
    try:
        data = json.loads(text)
        if "action" in data:
            return data
    except json.JSONDecodeError:
        pass

    # Look for JSON within markdown code blocks
    import re
    json_blocks = re.findall(r"```(?:json)?\s*\n?({.*?})\s*\n?```", text, re.DOTALL)
    for block in json_blocks:
        try:
            data = json.loads(block)
            if "action" in data:
                return data
        except json.JSONDecodeError:
            continue

    # Last attempt: find a JSON object anywhere in the text
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            data = json.loads(text[brace_start : brace_end + 1])
            if "action" in data:
                return data
        except json.JSONDecodeError:
            pass

    return None
