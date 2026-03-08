"""
Chat router — the main /chat endpoint that ties the LLM agent, service
router, conversation history, and Supabase persistence together.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_user
from app.supabase_client import get_supabase
from app.bot.agent import query_llm, parse_action
from app.bot.router import execute_action

router = APIRouter()


class ChatRequest(BaseModel):
    chat_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    service_result: dict | None = None
    escalated: bool = False
    chat_id: str = ""


def _save_message(chat_id: str, role: str, content: str):
    """Persist a single message to Supabase."""
    sb = get_supabase()
    sb.table("messages").insert(
        {"chat_id": chat_id, "role": role, "content": content}
    ).execute()


def _load_conversation(chat_id: str) -> list[dict]:
    """Load all messages for a chat as a conversation list."""
    sb = get_supabase()
    result = (
        sb.table("messages")
        .select("role, content")
        .eq("chat_id", chat_id)
        .order("created_at", desc=False)
        .execute()
    )
    return [{"role": m["role"], "content": m["content"]} for m in result.data]


def _auto_title(chat_id: str, user_message: str):
    """Set the chat title from the first user message (max 60 chars)."""
    sb = get_supabase()
    chat = sb.table("chats").select("title").eq("id", chat_id).single().execute()
    if chat.data and chat.data.get("title") == "New Chat":
        title = user_message[:60] + ("…" if len(user_message) > 60 else "")
        sb.table("chats").update({"title": title}).eq("id", chat_id).execute()


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    """
    Main conversational endpoint.
    1. Save user message to DB.
    2. Load full conversation history.
    3. Forward to LLM.
    4. If action detected, execute service.
    5. Save assistant response to DB.
    6. Return the final reply.
    """
    chat_id = req.chat_id
    user_id = user["id"]

    # Verify chat ownership
    sb = get_supabase()
    chat_check = (
        sb.table("chats")
        .select("id")
        .eq("id", chat_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not chat_check.data:
        return ChatResponse(reply="Chat not found.", chat_id=chat_id)

    # Step 1 — Save user message
    _save_message(chat_id, "user", req.message)
    _auto_title(chat_id, req.message)

    # Step 2 — Load full conversation history
    history = _load_conversation(chat_id)

    # Step 3 — Ask the LLM
    llm_reply = await query_llm(history)

    # Step 4 — Check if the LLM returned a tool-call action
    action = parse_action(llm_reply)

    if action:
        action_name = action.get("action", "")
        entities = action.get("entities", {})

        # Pass user_id for service request tracking
        entities["_user_id"] = user_id

        result = await execute_action(action_name, entities)

        if result.get("success"):
            # Ask the LLM to compose a friendly reply from the service data
            follow_up = (
                f"Here is the result from the {result.get('service', 'service')} lookup:\n\n"
                f"{result['summary']}\n\n"
                "Please present this information clearly to the user in a friendly, "
                "easy-to-understand format. Include the policy reference."
            )
            history.append({"role": "assistant", "content": llm_reply})
            history.append({"role": "user", "content": follow_up})
            final_reply = await query_llm(history)

            # Step 5 — Save assistant response
            _save_message(chat_id, "assistant", final_reply)
            return ChatResponse(
                reply=final_reply,
                service_result=result.get("data"),
                chat_id=chat_id,
            )
        else:
            error_msg = result.get("message", "Something went wrong.")
            _save_message(chat_id, "assistant", error_msg)
            return ChatResponse(reply=error_msg, chat_id=chat_id)

    # Step 5b — No action; the LLM reply is the response
    escalation_keywords = ["human officer", "escalate", "connect you to", "transfer"]
    escalated = any(kw in llm_reply.lower() for kw in escalation_keywords)

    _save_message(chat_id, "assistant", llm_reply)
    return ChatResponse(reply=llm_reply, escalated=escalated, chat_id=chat_id)
