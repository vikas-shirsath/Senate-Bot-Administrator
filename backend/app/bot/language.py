"""
Language detection utility using langdetect.
"""

from langdetect import detect, LangDetectException

SUPPORTED_LANGS = {"en", "hi", "mr", "te"}

LANG_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "te": "Telugu",
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
        # langdetect returns ISO 639-1 codes
        if detected in SUPPORTED_LANGS:
            return detected
        # Fallback: langdetect sometimes returns 'hi' for Marathi since
        # both use Devanagari. We keep the detected code if supported.
        return "en"
    except LangDetectException:
        return "en"
