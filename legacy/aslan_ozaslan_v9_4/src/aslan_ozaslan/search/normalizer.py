from __future__ import annotations
import re
import unicodedata

class QueryNormalizer:
    TURKISH_MAP = str.maketrans({
        "İ": "i", "I": "i", "ı": "i",
        "Ş": "s", "ş": "s",
        "Ğ": "g", "ğ": "g",
        "Ü": "u", "ü": "u",
        "Ö": "o", "ö": "o",
        "Ç": "c", "ç": "c",
    })

    def normalize(self, text: str) -> str:
        if not text or not text.strip():
            return ""
        value = unicodedata.normalize("NFKC", text).translate(self.TURKISH_MAP).lower()
        value = re.sub(r"[^a-z0-9\s-]", " ", value)
        value = re.sub(r"\s+", " ", value).strip()
        return value

    def tokens(self, text: str) -> tuple[str, ...]:
        normalized = self.normalize(text)
        return tuple(token for token in normalized.split() if len(token) >= 2)
