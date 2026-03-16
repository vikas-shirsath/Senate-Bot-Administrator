"""
Chat router — /chat/text and /chat/voice endpoints implementing the full
multilingual pipeline: detect→translate→LLM→translate→store→respond.
"""

import base64
import re
from fastapi import APIRouter, Depends, UploadFile, File, Form
from pydantic import BaseModel

from app.auth import get_current_user
from app.supabase_client import get_supabase
from app.bot.agent import query_llm, parse_action
from app.bot.router import execute_action
from app.bot.language import detect_language, LANG_NAMES
from app.services.reverie import speech_to_text, translate, text_to_speech

router = APIRouter()


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting so TTS speaks clean natural text."""
    # Remove bold/italic markers
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
    # Remove headings
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    # Remove inline code / backticks
    text = re.sub(r"`{1,3}.*?`{1,3}", "", text, flags=re.DOTALL)
    # Remove links [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove bullet points
    text = re.sub(r"^\s*[-*•]\s+", "", text, flags=re.MULTILINE)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()



# ── Request / Response models ────────────────────────────

class TextChatRequest(BaseModel):
    chat_id: str
    message: str
    preferred_language: str = "en"


class ChatResponse(BaseModel):
    reply: str
    service_result: dict | None = None
    escalated: bool = False
    chat_id: str = ""
    detected_language: str = "en"
    audio_base64: str | None = None
    input_type: str = "text"
    original_text: str = ""


# ── Persistence helpers ──────────────────────────────────

def _save_message(
    chat_id: str,
    role: str,
    content: str,
    input_type: str = "text",
    original_language: str = "en",
    original_text: str = "",
    translated_english: str = "",
    response_english: str = "",
    response_hindi: str = "",
    response_marathi: str = "",
    audio_url: str = "",
):
    """Persist a single message with multilingual fields."""
    sb = get_supabase()
    sb.table("messages").insert({
        "chat_id": chat_id,
        "role": role,
        "content": content,
        "input_type": input_type,
        "original_language": original_language,
        "original_text": original_text,
        "translated_english": translated_english,
        "response_english": response_english,
        "response_hindi": response_hindi,
        "response_marathi": response_marathi,
        "audio_url": audio_url,
    }).execute()


def _load_conversation(chat_id: str) -> list[dict]:
    """Load all messages for a chat as a conversation list (English text)."""
    sb = get_supabase()
    result = (
        sb.table("messages")
        .select("role, content, translated_english, response_english")
        .eq("chat_id", chat_id)
        .order("created_at", desc=False)
        .execute()
    )
    conversation = []
    for m in result.data:
        if m["role"] == "user":
            # Use the English translation for LLM context
            text = m.get("translated_english") or m["content"]
            conversation.append({"role": "user", "content": text})
        else:
            # Use English response for LLM context
            text = m.get("response_english") or m["content"]
            conversation.append({"role": "assistant", "content": text})
    return conversation


def _auto_title(chat_id: str, user_message: str):
    """Set the chat title from the first user message (max 60 chars)."""
    sb = get_supabase()
    chat = sb.table("chats").select("title").eq("id", chat_id).single().execute()
    if chat.data and chat.data.get("title") == "New Chat":
        title = user_message[:60] + ("…" if len(user_message) > 60 else "")
        sb.table("chats").update({"title": title}).eq("id", chat_id).execute()


# ── Translate to all three languages ─────────────────────

async def _translate_to_all(english_text: str) -> dict:
    """Translate English text to Hindi and Marathi. Returns dict with all 3."""
    hi_text = await translate(english_text, "en", "hi")
    mr_text = await translate(english_text, "en", "mr")
    return {
        "en": english_text,
        "hi": hi_text,
        "mr": mr_text,
    }


# ── Core chat processing pipeline ────────────────────────

async def _process_chat(
    chat_id: str,
    user_id: str,
    user_text: str,
    detected_lang: str,
    input_type: str = "text",
    preferred_language: str = "en",
) -> ChatResponse:
    """
    The core pipeline shared by text and voice endpoints.
    1. Translate user text to English
    2. Send to LLM
    3. Handle action / plain reply
    4. Translate response to all languages
    5. Store and return
    """

    # Determine reply language
    reply_lang = preferred_language if preferred_language != "en" else detected_lang

    # Step 1 — Translate user input to English
    if detected_lang != "en":
        english_text = await translate(user_text, detected_lang, "en")
    else:
        english_text = user_text

    # Save user message
    _save_message(
        chat_id=chat_id,
        role="user",
        content=user_text,
        input_type=input_type,
        original_language=detected_lang,
        original_text=user_text,
        translated_english=english_text,
    )
    _auto_title(chat_id, user_text)

    # Step 2 — Load conversation in English and query LLM
    history = _load_conversation(chat_id)
    llm_reply = await query_llm(history)

    # Step 3 — Check for tool-call action
    action = parse_action(llm_reply)
    final_english = llm_reply

    service_result = None

    if action:
        action_name = action.get("action", "")
        entities = action.get("entities", {})
        entities["_user_id"] = user_id

        result = await execute_action(action_name, entities)

        if result.get("success"):
            service_result = result.get("data")
            # Ask LLM to present the result nicely
            follow_up = (
                f"Here is the result from the {result.get('service', 'service')} lookup:\n\n"
                f"{result['summary']}\n\n"
                "Please present this information clearly to the user in a friendly, "
                "easy-to-understand format. Include the policy reference. Respond in English."
            )
            history.append({"role": "assistant", "content": llm_reply})
            history.append({"role": "user", "content": follow_up})
            final_english = await query_llm(history)
        else:
            final_english = result.get("message", "Something went wrong.")

    # Step 4 — Translate response to all languages
    translations = await _translate_to_all(final_english)

    # Pick reply in user's language
    reply_text = translations.get(reply_lang, final_english)

    # Step 5 — Escalation check
    escalation_keywords = ["human officer", "escalate", "connect you to", "transfer"]
    escalated = any(kw in final_english.lower() for kw in escalation_keywords)

    # Step 6 — Save assistant message
    _save_message(
        chat_id=chat_id,
        role="assistant",
        content=reply_text,
        original_language="en",
        original_text=final_english,
        translated_english=final_english,
        response_english=translations["en"],
        response_hindi=translations["hi"],
        response_marathi=translations["mr"],
    )

    return ChatResponse(
        reply=reply_text,
        service_result=service_result,
        escalated=escalated,
        chat_id=chat_id,
        detected_language=detected_lang,
        input_type=input_type,
        original_text=user_text,
    )


# ── POST /chat/text ──────────────────────────────────────

@router.post("/text", response_model=ChatResponse)
async def chat_text(req: TextChatRequest, user: dict = Depends(get_current_user)):
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

    # Detect language
    detected_lang = detect_language(req.message)

    return await _process_chat(
        chat_id=chat_id,
        user_id=user_id,
        user_text=req.message,
        detected_lang=detected_lang,
        input_type="text",
        preferred_language=req.preferred_language,
    )


# ── POST /chat/voice ─────────────────────────────────────

@router.post("/voice", response_model=ChatResponse)
async def chat_voice(
    audio: UploadFile = File(...),
    chat_id: str = Form(...),
    preferred_language: str = Form("en"),
    user: dict = Depends(get_current_user),
):
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

    # Read audio bytes
    audio_bytes = await audio.read()

    # Determine audio format from filename
    filename = audio.filename or "audio.webm"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "webm"

    # Step 1 — STT: Convert voice to text
    # Try with preferred language first, then auto-detect
    src_lang = preferred_language if preferred_language in ("hi", "mr", "en") else "hi"
    transcribed_text = await speech_to_text(audio_bytes, src_lang=src_lang, audio_format=ext)

    if not transcribed_text:
        return ChatResponse(
            reply="Sorry, I could not understand the audio. Please try again or type your message.",
            chat_id=chat_id,
            input_type="voice",
        )

    # Step 2 — Detect language of transcribed text
    detected_lang = detect_language(transcribed_text)

    # Step 3-6 — Process through pipeline
    response = await _process_chat(
        chat_id=chat_id,
        user_id=user_id,
        user_text=transcribed_text,
        detected_lang=detected_lang,
        input_type="voice",
        preferred_language=preferred_language,
    )

    # Step 7 — TTS: Convert response to audio
    # Strip markdown formatting so TTS speaks clean text
    reply_lang = preferred_language if preferred_language != "en" else detected_lang
    tts_audio = await text_to_speech(_strip_markdown(response.reply), lang=reply_lang)

    if tts_audio:
        audio_b64 = base64.b64encode(tts_audio).decode("utf-8")
        response.audio_base64 = f"data:audio/wav;base64,{audio_b64}"

    response.original_text = transcribed_text
    return response



# ── Legacy endpoint (backwards compat) ───────────────────

@router.post("", response_model=ChatResponse)
async def chat_legacy(req: TextChatRequest, user: dict = Depends(get_current_user)):
    """Backwards-compatible endpoint that forwards to /chat/text logic."""
    return await chat_text(req, user)


# ── On-demand TTS endpoint ───────────────────────────────

class TTSRequest(BaseModel):
    text: str
    lang: str = "en"


class TTSResponse(BaseModel):
    audio_base64: str | None = None
    error: str | None = None


@router.post("/tts", response_model=TTSResponse)
async def on_demand_tts(req: TTSRequest, user: dict = Depends(get_current_user)):
    """Generate TTS audio for any text on demand (speaker icon click)."""
    clean_text = _strip_markdown(req.text)
    if not clean_text.strip():
        return TTSResponse(error="No text to speak.")

    audio_bytes = await text_to_speech(clean_text, lang=req.lang)
    if audio_bytes:
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return TTSResponse(audio_base64=f"data:audio/wav;base64,{audio_b64}")

    return TTSResponse(error="TTS failed. Please try again.")

