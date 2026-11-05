import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FILES = ("premise", "characters", "world", "timeline", "locations", "terminology", "style_guide")

def load_project(root: str | Path) -> dict[str, Any]:
    base = Path(root)
    result = {}
    for name in FILES:
        path = base / f"{name}.json"
        result[name] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return result

def propose_change(root: str | Path, file_name: str, change: dict[str, Any], reason: str) -> dict[str, Any]:
    base = Path(root); base.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "file": file_name,
             "change": change, "reason": reason, "status": "proposed"}
    log = base / "decisions.log"
    with log.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry

def commit_change(root: str | Path, file_name: str, value: dict[str, Any], reason: str,
                  author_approved: bool = False, source: str | None = None) -> None:
    if not author_approved:
        raise PermissionError("Biblioteka wymaga jawnego zatwierdzenia autora.")
    if not source:
        raise ValueError("Każda zatwierdzona zmiana musi mieć źródło.")
    base = Path(root); base.mkdir(parents=True, exist_ok=True)
    path = base / file_name
    value = {**value, "version": int(value.get("version", 0)) + 1}
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "file": file_name,
             "reason": reason, "source": source, "status": "committed", "version": value["version"]}
    with (base / "decisions.log").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
