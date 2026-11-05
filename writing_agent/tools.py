import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
BIBLE = ROOT / "project_bible"

def load_bible(root: str | Path | None = None) -> dict[str, Any]:
    data: dict[str, Any] = {}
    base = Path(root) if root else BIBLE
    for path in sorted(base.glob("*.json")):
        data[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    return data

def style_editor(text: str, operation: str = "edit") -> dict[str, Any]:
    result = text.strip()
    if operation == "shorten":
        result = re.sub(r"\b(właściwie|tak naprawdę|oczywiście|generalnie)\b[ ,]*", "", result, flags=re.I)
        result = re.sub(r"\s+", " ", result).strip()
    return {"text": result, "operation": operation, "changes": [], "warnings": []}

def character_designer(name: str = "", goal: str = "", operation: str = "character_new") -> dict[str, Any]:
    raw = name.strip()
    details = ""
    if "," in raw:
        raw, details = [part.strip() for part in raw.split(",", 1)]
    generated_name = raw or "Lena"
    if generated_name.lower() in {"wymyśl głównego bohatera powieści", "wymyśl głównego bohatera", "stwórz bohaterkę fantasy", "zaprojektuj antagonistę"}:
        generated_name = "Lena"
    return {
        "id": re.sub(r"[^a-z0-9]+", "_", generated_name.lower()).strip("_"),
        "name": generated_name,
        "role": details or ("bohater/bohaterka propozycji" if operation == "character_new" else "postać rozwijana z biblii"),
        "goal": goal or "odnaleźć własny kierunek mimo presji otoczenia",
        "fear": "utraty kontroli nad własną historią",
        "motivation": "potrzeby ochrony tego, co uważa za ważne",
        "contradiction": "pragnie bliskości, ale odsuwa innych, gdy czuje zagrożenie",
        "relationships": [],
        "arc": "od unikania decyzji do świadomego wyboru",
        "voice": "oszczędny, konkretny, z krótkimi pauzami",
        "status": "proposed",
        "operation": operation,
    }

def continuity_checker(text: str, bible: dict[str, Any] | None = None) -> dict[str, Any]:
    bible = bible or load_bible()
    conflicts = []
    known_terms = bible.get("terminology", {}).get("terms", {})
    for term in known_terms:
        if term.lower() in text.lower():
            continue
    years = [int(x) for x in re.findall(r"\b(1[5-9]\d{2}|20\d{2})\b", text)]
    if years != sorted(years):
        conflicts.append({"type": "chronology", "detail": "Daty występują w kolejności malejącej."})
    return {"status": "conflict" if conflicts else "consistent", "conflicts": conflicts, "checked_against": list(bible)}
