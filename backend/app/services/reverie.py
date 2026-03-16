"""
Speech & Translation API Integration Layer
- Speech-to-Text (STT) → Sarvam AI (Saaras v3)
- Text-to-Speech (TTS) → Sarvam AI (Bulbul v3)
- Translation         → Reverie (Localization API)
"""

import os
import base64
import httpx

# ══════════════════════════════════════════════════════════
# Sarvam AI — TTS & STT
# ══════════════════════════════════════════════════════════

SARVAM_BASE = "https://api.sarvam.ai"

_SARVAM_LANG_CODES = {
    "en": "en-IN",
    "hi": "hi-IN",
    "mr": "mr-IN",
}

_SPEAKERS = {
    "en": "sophia",
    "hi": "priya",
    "mr": "kavya",
}


def _sarvam_header() -> dict:
    return {"API-Subscription-Key": os.getenv("SARVAM_API_KEY", "")}


async def speech_to_text(audio_bytes: bytes, src_lang: str = "hi", audio_format: str = "wav") -> str:
    """Sarvam STT — convert audio to text using Saaras v3."""
    lang_code = _SARVAM_LANG_CODES.get(src_lang, "hi-IN")
    mime = f"audio/{audio_format}" if audio_format != "webm" else "audio/webm"

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{SARVAM_BASE}/speech-to-text",
                headers=_sarvam_header(),
                files={"file": (f"audio.{audio_format}", audio_bytes, mime)},
                data={"model": "saaras:v3", "language_code": lang_code},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("transcript", "")
    except Exception as e:
        import traceback
        print(f"[Sarvam STT Error] {type(e).__name__}: {e}")
        traceback.print_exc()
        return ""


async def text_to_speech(text: str, lang: str = "hi") -> bytes | None:
    """Sarvam TTS — convert text to WAV audio using Bulbul v3."""
    # Truncate long text to avoid timeouts
    MAX_TTS_CHARS = 500
    tts_text = text
    if len(tts_text) > MAX_TTS_CHARS:
        cut = tts_text[:MAX_TTS_CHARS]
        for sep in ["।", ".", "!", "?"]:
            last = cut.rfind(sep)
            if last > MAX_TTS_CHARS // 2:
                cut = cut[: last + 1]
                break
        tts_text = cut

    lang_code = _SARVAM_LANG_CODES.get(lang, "en-IN")
    speaker = _SPEAKERS.get(lang, "sophia")

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{SARVAM_BASE}/text-to-speech",
                headers={**_sarvam_header(), "Content-Type": "application/json"},
                json={
                    "text": tts_text,
                    "target_language_code": lang_code,
                    "model": "bulbul:v3",
                    "speaker": speaker,
                },
            )
            print(f"[Sarvam TTS] Status: {resp.status_code}, Size: {len(resp.content)} bytes")

            if resp.status_code != 200:
                print(f"[Sarvam TTS Error] HTTP {resp.status_code}: {resp.text[:500]}")
                return None

            data = resp.json()
            audios = data.get("audios", [])
            if audios:
                return base64.b64decode(audios[0])

            print(f"[Sarvam TTS Error] No audios in response")
            return None
    except Exception as e:
        import traceback
        print(f"[Sarvam TTS Error] {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


# ══════════════════════════════════════════════════════════
# Reverie — Translation
# ══════════════════════════════════════════════════════════

REVERIE_BASE = "https://revapi.reverieinc.com/"


def _reverie_headers() -> dict:
    return {
        "REV-API-KEY": os.getenv("REVERIE_API_KEY", ""),
        "REV-APP-ID": os.getenv("REVERIE_APP_ID", "com.white2tiger57"),
    }


async def translate(text: str, src_lang: str, tgt_lang: str) -> str:
    """Reverie Translation — localization API."""
    if src_lang == tgt_lang or not text.strip():
        return text

    headers = {
        **_reverie_headers(),
        "REV-APPNAME": "localization",
        "REV-APPVERSION": "3.0",
        "Content-Type": "application/json",
        "src_lang": src_lang,
        "tgt_lang": tgt_lang,
        "domain": "generic",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                REVERIE_BASE,
                headers=headers,
                json={"data": [text]},
            )
            resp.raise_for_status()
            data = resp.json()
            response_list = data.get("responseList", [])
            if response_list:
                return response_list[0].get("outString", text)
            return text
    except Exception as e:
        print(f"[Reverie Translation Error] {type(e).__name__}: {e}")
        return text
