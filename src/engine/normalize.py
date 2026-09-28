"""Text and time helpers used on X posts: language detection (X marks many posts "und") and time parsing.
Ingestion itself is engine/xstore.py: X API v2 JSON only."""
import re
from datetime import datetime, timezone

# ponytail: 05/09/2020 is read month-first (US exports); day-first is used only when the first number is over 12
TIME_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y",
                "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y",
                "%a %b %d %H:%M:%S %z %Y", "%d %b %Y %H:%M", "%d %B %Y %H:%M", "%b %d, %Y %I:%M %p"]
URL_RE = re.compile(r"https?://\S+")
# \w alone stops at vowel signs and other combining marks, which cut "#कोरोना" to "#क"
HASHTAG_RE = re.compile(r"#[\w\u0300-\u036F\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0900-\u0DFF\u0E00-\u0E7F]+")
# Non-Latin scripts name the language well enough for triage (Cyrillic is reported as Russian, Arabic script with
# Urdu letters as Urdu). Checked in this order: Japanese kana before Chinese characters, which Japanese also uses.
SCRIPTS = [
    ("hi", r"[\u0900-\u097F]"), ("bn", r"[\u0980-\u09FF]"), ("pa", r"[\u0A00-\u0A7F]"), ("gu", r"[\u0A80-\u0AFF]"),
    ("or", r"[\u0B00-\u0B7F]"), ("ta", r"[\u0B80-\u0BFF]"), ("te", r"[\u0C00-\u0C7F]"), ("kn", r"[\u0C80-\u0CFF]"),
    ("ml", r"[\u0D00-\u0D7F]"), ("ur", r"[\u0679\u0688\u0691\u06BA\u06BE\u06C1\u06D2]"), ("ar", r"[\u0600-\u06FF]"),
    ("ru", r"[\u0400-\u04FF]"), ("el", r"[\u0370-\u03FF]"), ("he", r"[\u0590-\u05FF]"), ("th", r"[\u0E00-\u0E7F]"),
    ("ja", r"[\u3040-\u30FF]"), ("ko", r"[\uAC00-\uD7AF]"), ("zh", r"[\u4E00-\u9FFF]"),
]
SCRIPT_RES = [(code, re.compile(pattern)) for code, pattern in SCRIPTS]
# Hindi in Roman script: needs at least one unambiguous word, so Spanish or Catalan "se", "ke" don't count
HINGLISH_STRONG = {"hai", "hain", "nahi", "nahin", "kya", "aaj", "bhai", "mein", "raha", "rahi", "rahe", "karo", "kar",
                   "aur", "bhi", "yeh", "woh", "abhi", "tum", "hum", "sabhi", "gaya", "gayi", "wala", "wali", "diya"}
HINGLISH_WEAK = {"ke", "ki", "ko", "se", "ye", "pe", "sab", "log", "kal"}
STOPWORDS = {  # the most frequent words of each language; the language with most hits (at least 2) wins
    "en": {"the", "and", "is", "are", "to", "of", "in", "for", "you", "this", "that", "with", "on", "it", "was", "be",
           "not", "have", "will", "they", "we", "at"},
    "es": {"el", "los", "las", "que", "y", "en", "por", "para", "con", "una", "es", "del", "se", "no", "lo", "como"},
    "ca": {"els", "les", "que", "i", "per", "amb", "una", "és", "del", "es", "no", "al", "més", "dels", "ho", "això"},
    "fr": {"le", "les", "et", "est", "des", "un", "une", "pour", "dans", "que", "qui", "pas", "du", "au", "sur"},
    "de": {"der", "die", "das", "und", "ist", "nicht", "mit", "ein", "eine", "zu", "den", "von", "auf", "sich"},
    "pt": {"os", "que", "e", "em", "para", "com", "um", "uma", "não", "do", "da", "dos", "se", "no"},
}


def detect_language(text: str) -> str | None:
    """Script first (Devanagari → hi, Cyrillic → ru, …); for Latin script, Hinglish words, then common words."""
    text = text or ""
    letters = re.sub(r"https?://\S+|[@#]\w+", "", text)
    for code, pattern in SCRIPT_RES:
        if len(pattern.findall(letters)) >= 3:
            return code
    words = re.findall(r"[a-z\u00E0-\u00FF]+", letters.lower())
    strong = sum(w in HINGLISH_STRONG for w in words)
    if strong and strong + sum(w in HINGLISH_WEAK for w in words) >= 2:
        return "hinglish"
    hits = {code: sum(w in stop for w in words) for code, stop in STOPWORDS.items()}
    best = max(hits, key=hits.get)
    return best if hits[best] >= 2 else ("en" if hits["en"] else None)


def parse_time(value, naive_zone=None) -> int | None:
    """Unix seconds from epoch seconds/milliseconds or a date string. Times without a zone are read in naive_zone
    (the dataset's local clock), UTC if none is given."""
    v = str(value if value is not None else "").strip()
    if not v:
        return None
    if re.fullmatch(r"\d+(\.\d+)?", v):
        t = float(v)
        return int(t / 1000 if t > 1e11 else t)  # 13-digit values are milliseconds
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        for fmt in TIME_FORMATS:
            try:
                dt = datetime.strptime(v, fmt)
                break
            except ValueError:
                continue
        else:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=naive_zone or timezone.utc)
    return int(dt.timestamp())
