from dataclasses import dataclass
import re

@dataclass(frozen=True)
class InputCheck:
    valid: bool
    clarification: str | None = None

def validate_input(intent: str, prompt: str) -> InputCheck:
    low = prompt.lower().strip()
    if intent in {"interpret", "check_style"}:
        has_quote = any(mark in prompt for mark in ('"', "„", "”", "'", "«", "»"))
        has_payload = bool(re.search(r"(?:fragment|tekst|zdanie|akapitu)\s*:\s*\S+", low))
        vague = low.endswith("...") or low.endswith("…") or any(x in low for x in ("w tym fragmencie", "tego fragmentu", "ten tekst"))
        if not has_quote and not has_payload and vague:
            return InputCheck(False, "Nie otrzymałem fragmentu. Wklej tekst, który mam zinterpretować lub przeanalizować.")
    return InputCheck(True)
