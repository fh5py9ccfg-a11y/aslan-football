from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Iterable, Mapping

# Verified public iddaa programme fixtures for 22 Aug 2026.
# Source set is intentionally explicit: matches not in this set are excluded.
_BULLETIN_2026_08_22 = {
    ("corum fk", "kasimpasa"),
    ("rizespor", "samsunspor"),
    ("fenerbahce", "konyaspor"),
    ("hull", "man united"),
    ("ipswich", "sunderland"),
    ("nott forest", "leeds utd"),
    ("everton", "cry palace"),
    ("brentford", "tottenham"),
    ("ath bilbao", "sevilla"),
    ("valencia", "celta vigo"),
    ("espanyol", "real madrid"),
    ("inter", "monza"),
    ("udinese", "como"),
    ("genoa", "napoli"),
    ("parma", "cagliari"),
    ("lens", "auxerre"),
    ("troyes", "paris fc"),
    ("nice", "lorient"),
    ("toulouse", "lyon"),
    ("le mans", "brest"),
    ("igdir fk", "kayserispor"),
    ("umraniyespor", "erokspor"),
    ("antalyaspor", "pendikspor"),
    ("bodrum", "muglaspor"),
    ("crusaders", "portadown fc"),
    ("sandnes", "bryne"),
    ("mtk", "nyiregyhaza"),
    ("tampere utd", "rops"),
    ("ammanford", "gap connahs qua"),
}

_ALIASES = {
    "manchester united": "man united",
    "man utd": "man united",
    "nottingham forest": "nott forest",
    "leeds united": "leeds utd",
    "crystal palace": "cry palace",
    "athletic bilbao": "ath bilbao",
    "internazionale": "inter",
    "inter milan": "inter",
    "corum": "corum fk",
    "kasimpasa sk": "kasimpasa",
    "caykur rizespor": "rizespor",
    "erokspor": "erokspor",
}


def _norm(value: object) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("ı", "i")
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return _ALIASES.get(text, text)


def bulletin_pairs(day: date) -> set[tuple[str, str]]:
    if day.isoformat() == "2026-08-22":
        return set(_BULLETIN_2026_08_22)
    return set()


def filter_to_bulletin(fixtures: Iterable[Mapping[str, object]], *, day: date) -> tuple[list[dict], int]:
    allowed = bulletin_pairs(day)
    if not allowed:
        return [], 0
    result: list[dict] = []
    for item in fixtures:
        home = _norm(item.get("home_team") or item.get("home_name"))
        away = _norm(item.get("away_team") or item.get("away_name"))
        if (home, away) in allowed:
            row = dict(item)
            row["bulletin_verified"] = True
            result.append(row)
    return result, len(allowed)
