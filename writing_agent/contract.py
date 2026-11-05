from dataclasses import dataclass
import re
from typing import Literal

Mode = Literal["creative", "factual", "mixed"]
OutputMode = Literal["TEXT_ONLY", "TEXT_WITH_NOTES", "ANALYSIS_ONLY", "STRUCTURED_JSON", "AUDIOBOOK_DIRECTOR"]
Intent = Literal[
    "create", "expand", "rewrite", "shorten", "edit", "plan",
    "check_continuity", "check_style", "check_facts", "interpret", "summarize",
]

@dataclass(frozen=True)
class RequestContract:
    intent: Intent
    mode: Mode
    text: str
    confidence: float
    output_mode: OutputMode

def classify_request(text: str, mode: Mode | None = None) -> RequestContract:
    low = text.lower()
    if any(k in low for k in ("audiobook", "scenariusz audio", "reżyseruj głos", "tts", "audioticon")):
        intent: Intent = "create"
    elif any(k in low for k in ("ciągłość", "spójność fabuły", "chronologi", "wiek bohater")) or ("sprawdź" in low and ("wiek" in low or re.search(r"\b\d+\s*lat", low))):
        intent: Intent = "check_continuity"
    elif any(k in low for k in ("zinterpretuj", "interpretacj", "podtekst", "metafor", "symbol", "znaczenie obrazu", "omów")):
        intent = "interpret"
    elif any(k in low for k in ("fakt", "źródł", "sprawdź, czy", "prawdziw", "potwierdzon", "biblia projektu")):
        intent = "check_facts"
    elif any(k in low for k in ("analizuj styl", "przeanalizuj ton", "oceń styl", "sprawdź styl")):
        intent = "check_style"
    elif any(k in low for k in ("skróć", "krócej", "zwięźl")):
        intent = "shorten"
    elif any(k in low for k in ("przeredaguj", "przepisz", "zredaguj")):
        intent = "rewrite"
    elif any(k in low for k in ("rozwiń", "rozbuduj", "dodaj szczegóły")):
        intent = "expand"
    elif any(k in low for k in ("plan", "logline", "rozdział", "konspekt")):
        intent = "plan"
    elif any(k in low for k in ("podsumuj", "streszcz")):
        intent = "summarize"
    else:
        intent = "create"
    selected_mode: Mode = mode or ("factual" if intent == "check_facts" else "creative")
    if any(k in low for k in ("audiobook", "scenariusz audio", "audioticon")):
        output_mode: OutputMode = "AUDIOBOOK_DIRECTOR"
    elif intent in {"check_style", "check_continuity", "check_facts", "interpret", "summarize"}:
        output_mode: OutputMode = "ANALYSIS_ONLY"
    else:
        output_mode = "TEXT_ONLY"
    if "osobno uwagi" in low or "dodaj uwagi" in low:
        output_mode = "TEXT_WITH_NOTES"
    if "json" in low and any(word in low for word in ("format", "formacie")):
        output_mode = "STRUCTURED_JSON"
    return RequestContract(intent=intent, mode=selected_mode, text=text, confidence=0.75, output_mode=output_mode)
