"""
Language detection utility using langdetect.
Scoped to English, Hindi, Marathi (project languages).
"""

from langdetect import detect, LangDetectException

SUPPORTED_LANGS = {"en", "hi", "mr"}

LANG_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
}

# Reverie language codes (same as ISO 639-1 for these)
REVERIE_LANG_CODES = {
    "en": "en",
    "hi": "hi",
    "mr": "mr",
}

# Reverie TTS speaker names
REVERIE_SPEAKERS = {
    "en": "en_female",
    "hi": "hi_female",
    "mr": "mr_female",
}

# DB column names for each language response
LANG_RESPONSE_COLUMNS = {
    "en": "response_english",
    "hi": "response_hindi",
    "mr": "response_marathi",
}


def detect_language(text: str) -> str:
    """
    Detect the language of the given text.
    Returns a supported language code or 'en' as fallback.
    """
    if not text or len(text.strip()) < 3:
        return "en"

    try:
        detected = detect(text)
        if detected in SUPPORTED_LANGS:
            return detected
        return "en"
    except LangDetectException:
        return "en"
