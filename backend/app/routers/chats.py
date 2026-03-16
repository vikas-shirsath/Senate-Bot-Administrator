"""
Chats router — CRUD endpoints for chat sessions and message history.
Supports multilingual message retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import get_current_user
from app.supabase_client import get_supabase

router = APIRouter()


class CreateChatRequest(BaseModel):
    title: str = "New Chat"


# Column mapping for language-specific responses
_LANG_COLUMNS = {
    "en": "response_english",
    "hi": "response_hindi",
    "mr": "response_marathi",
}


# ── List all chats for the current user ──────────────────
@router.get("")
async def list_chats(user: dict = Depends(get_current_user)):
    sb = get_supabase()
    result = (
        sb.table("chats")
        .select("*")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


# ── Create a new chat ────────────────────────────────────
@router.post("")
async def create_chat(
    body: CreateChatRequest,
    user: dict = Depends(get_current_user),
):
    sb = get_supabase()
    result = (
        sb.table("chats")
        .insert({"user_id": user["id"], "title": body.title})
        .execute()
    )
    return result.data[0]


# ── Get messages for a chat ──────────────────────────────
@router.get("/{chat_id}/messages")
async def get_messages(
    chat_id: str,
    lang: str = Query("en", description="Language for response display"),
    user: dict = Depends(get_current_user),
):
    sb = get_supabase()
    # Verify the chat belongs to the user
    chat = (
        sb.table("chats")
        .select("id")
        .eq("id", chat_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not chat.data:
        raise HTTPException(404, "Chat not found")

    messages = (
        sb.table("messages")
        .select("*")
        .eq("chat_id", chat_id)
        .order("created_at", desc=False)
        .execute()
    )

    # Format messages with language-appropriate content
    lang_col = _LANG_COLUMNS.get(lang, "response_english")
    formatted = []
    for m in messages.data:
        if m["role"] == "user":
            # Show original text for user messages
            content = m.get("original_text") or m.get("content", "")
        else:
            # Show language-specific response for assistant messages
            content = m.get(lang_col) or m.get("content", "")

        formatted.append({
            **m,
            "content": content,
        })

    return formatted


# ── Update chat title ────────────────────────────────────
@router.patch("/{chat_id}")
async def update_chat(chat_id: str, body: CreateChatRequest, user: dict = Depends(get_current_user)):
    sb = get_supabase()
    result = (
        sb.table("chats")
        .update({"title": body.title})
        .eq("id", chat_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Chat not found")
    return result.data[0]


# ── Delete a chat (cascades to messages) ─────────────────
@router.delete("/{chat_id}")
async def delete_chat(chat_id: str, user: dict = Depends(get_current_user)):
    sb = get_supabase()
    result = (
        sb.table("chats")
        .delete()
        .eq("id", chat_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Chat not found")
    return {"status": "deleted"}
