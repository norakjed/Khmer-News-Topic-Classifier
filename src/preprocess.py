"""Shared preprocessing. Cleaning only - nothing here is fit on data."""
import re
import unicodedata

URL_RE = re.compile(r"https?://\S+|www\.\S+")
ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff"), None)
KHMER_RE = re.compile(r"[\u1780-\u17FF]")


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFC", str(text))
    text = text.translate(ZERO_WIDTH)
    text = URL_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # lowercase Latin letters only (Khmer has no case)
    return "".join(c.lower() if c.isascii() else c for c in text)


def khmer_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    return len(KHMER_RE.findall(text)) / len(letters) if letters else 0.0
