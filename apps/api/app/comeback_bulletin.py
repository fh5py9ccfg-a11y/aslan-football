from __future__ import annotations

import re
import unicodedata
from datetime import date
from difflib import SequenceMatcher
from typing import Iterable, Mapping

_BULLETIN_2026_08_22 = {
    ("rizespor","samsunspor"),("corum","kasimpasa"),("breda","ajax b"),("dundee united","dundee"),
    ("ammanford","gap connahs qua"),("crusaders","portadown fc"),("carrick rangers","coleraine"),("dungannon","bangor fc"),
    ("club brugge ii","rfc seraing"),("zemplin","skalica"),("longford","bray wanderers"),("dila gori","torpedo kutaisi"),
    ("spaeri","samgurali"),("crewe","northampton"),("rotherham","york"),("walsall","grimsby"),
    ("bristol rovers","newport county"),("exeter","accrington"),("queens park","stenhousemuir"),("morton","arbroath"),
    ("livingston","dunfermline"),("al orubah club","al raed"),("al taee","al akhdoud"),("al najma","al jandal"),
    ("annagh united","moyola park"),("ards fc","loughgall fc"),("queens university","institute fc"),("strabane athletic","hw welders"),
    ("newington yc","rathfriland rangers"),("solihull moors","southend"),("eastleigh","scunthorpe"),("woking","afc fylde"),
    ("carlisle","hornchurch"),("forest green","boreham wood"),("harrogate","barrow"),("yeovil","gateshead"),
    ("hume city","caroline springs"),("olympic kingsway","fremantle city"),("stirling lions","western knights"),
    ("cham","grand saconnex"),("paradiso","fc kreuzlingen"),("luzern ii","bulle"),("east fife","hamilton"),
    ("cove rangers","peterhead"),("airdrieonians","ross county"),("queen of south","alloa"),("montrose","east kilbride"),
    ("edinburgh city","annan"),("spartans","elgin"),("stirling albion","stranraer"),("clyde","forfar"),("kelty hearts","dumbarton")
}

_ALIASES = {
    "dundee utd":"dundee united","dundee united fc":"dundee united",
    "carrick ranger":"carrick rangers","bangor":"bangor fc","portadown":"portadown fc",
    "queens univers":"queens university","strabane athle":"strabane athletic",
    "rathfriland ran":"rathfriland rangers","olympic kingsw":"olympic kingsway",
    "caroline s":"caroline springs","edinburg c":"edinburgh city",
    "stirling albio":"stirling albion","gap connahs quay":"gap connahs qua",
    "corum fk":"corum","caykur rizespor":"rizespor","kasimpasa sk":"kasimpasa",
    "queen s park":"queens park","queen of the south":"queen of south",
    "forest green rovers":"forest green","newport county afc":"newport county",
    "bray wanderers fc":"bray wanderers","rfc seraing united":"rfc seraing",
}

_DROP_TOKENS = {"fc","fk","sk","afc","cf","club","football","futbol","sc","ac"}


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
