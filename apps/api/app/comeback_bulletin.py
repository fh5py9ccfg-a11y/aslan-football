from __future__ import annotations

import re
import unicodedata
from datetime import date
from difflib import SequenceMatcher
from typing import Iterable, Mapping

# Verified from the 22 Aug 2026 public Iddaa programme archive.
# Only fixtures observed in that programme are allowed here.
_BULLETIN_2026_08_22 = {
    ("rizespor", "samsunspor"),
    ("corum", "kasimpasa"),
    ("fenerbahce", "konyaspor"),
    ("ipswich", "sunderland"),
    ("brentford", "tottenham"),
    ("nottingham f", "leeds utd"),
    ("eldense", "cadiz"),
    ("albacete", "real sociedad i"),
    ("ceuta", "las palmas"),
    ("aek", "iraklis 1908"),
    ("olympiakos", "atromitos"),
    ("orgryte", "halmstads"),
    ("sd rsa", "hong kong fc"),
    ("buler rangers", "kitchee footbal"),
    ("tampere utd", "rops"),
    ("chichester cit", "chippenham town"),
    ("frome town", "gosport borough"),
    ("hanworth villa", "evesham united"),
    ("basingstoke", "bath city"),
    ("dundee united", "dundee"),
}

_ALIASES = {
    "corum fk": "corum",
    "caykur rizespor": "rizespor",
    "kasimpasa sk": "kasimpasa",
    "fenerbahce sk": "fenerbahce",
    "nottingham forest": "nottingham f",
    "nottingham forest fc": "nottingham f",
    "leeds united": "leeds utd",
    "dundee utd": "dundee united",
    "dundee united fc": "dundee united",
    "athletic club ceuta": "ceuta",
    "las palmas ud": "las palmas",
    "olympiacos": "olympiakos",
    "iraklis": "iraklis 1908",
    "tampere united": "tampere utd",
    "rovanimen palloseura": "rops",
}

_DROP_TOKENS = {"fc", "fk", "sk", "afc", "cf", "club", "football", "futbol", "sc", "ac"}


def _norm(value: object) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("ı", "i")
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return _ALIASES.get(text, text)


def _core(text: str) -> str:
    n = _norm(text)
    tokens = [t for t in n.split() if t not in _DROP_TOKENS]
    return " ".join(tokens) or n


def _team_match(a: str, b: str) -> bool:
    a0, b0 = _norm(a), _norm(b)
    if a0 == b0:
        return True
    a1, b1 = _core(a0), _core(b0)
    if a1 == b1:
        return True
    if min(len(a1), len(b1)) >= 5 and (a1 in b1 or b1 in a1):
        return True
    return SequenceMatcher(None, a1, b1).ratio() >= 0.84


def bulletin_pairs(day: date) -> set[tuple[str, str]]:
    return set(_BULLETIN_2026_08_22) if day.isoformat() == "2026-08-22" else set()


def filter_to_bulletin(fixtures: Iterable[Mapping[str, object]], *, day: date) -> tuple[list[dict], int]:
    allowed = bulletin_pairs(day)
    result: list[dict] = []
    for item in fixtures:
        home = str(item.get("home_team") or item.get("home_name") or "")
        away = str(item.get("away_team") or item.get("away_name") or "")
        matched_pair = next(
            ((bh, ba) for bh, ba in allowed if _team_match(home, bh) and _team_match(away, ba)),
            None,
        )
        if matched_pair:
            row = dict(item)
            row["bulletin_verified"] = True
            row["bulletin_match"] = {"home": matched_pair[0], "away": matched_pair[1]}
            result.append(row)
    return result, len(allowed)
