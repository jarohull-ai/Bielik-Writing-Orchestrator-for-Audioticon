import re
from dataclasses import dataclass

META_NAMES = r"tone|ton|voice|style|styl|avoid|uwagi(?:\s+redakcyjne)?|metakomentarz|edytor(?:\s*\(uwagi\))?|oryginalny tekst[^:]*|krótsza wersja[^:]*|dynamiczna skrócona wersja[^:]*"
META_LABEL = re.compile(rf"^\s*(?:\*\*|__)?(?:{META_NAMES})(?:\s*\([^)]*\))?\s*:\s*(?:\*\*|__)?\s*", re.I | re.M)
SECTION_LABEL = re.compile(r"^\s*(?:\*\*|__)?(?:uwagi(?:\s+redakcyjne)?|edytor|oryginalny tekst|krótsza wersja|dynamiczna skrócona wersja)[^:]*\s*:\s*(?:\*\*|__)?", re.I)
META_PHRASE = re.compile(r"^\s*(oto tekst|poniżej znajduje się|mam nadzieję, że)\b[\s:,-]*", re.I)
META_TRAILER = re.compile(r"^\s*(?:\*\*|__)?[\[(]?(uwaga(?: redakcyjna)?|notatka|komentarz)\s*:\s*(?:\*\*|__)?[^\n]*[\])]?$", re.I)

@dataclass(frozen=True)
class RenderResult:
    text: str
    metadata_detected: bool
    cleaned: bool
    confidence: float
    warning: str | None = None

def _looks_like_metadata(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    label_lines = sum(bool(META_LABEL.match(line)) for line in lines)
    standalone_label = any(bool(META_LABEL.match(line)) and not line.startswith(("—", "-", "„", '"')) for line in lines)
    return bool(META_PHRASE.search(text) or any(META_TRAILER.match(line) for line in lines) or any(SECTION_LABEL.match(line) for line in lines) or label_lines >= 2 or (label_lines == 1 and standalone_label and len(lines) <= 3))

def render(text: str, output_mode: str) -> RenderResult:
    if output_mode != "TEXT_ONLY":
        return RenderResult(text=text.strip(), metadata_detected=False, cleaned=False, confidence=1.0)
    original = text.strip()
    if not _looks_like_metadata(original):
        return RenderResult(text=original, metadata_detected=False, cleaned=False, confidence=0.98)
    cleaned = original
    cleaned = META_PHRASE.sub("", cleaned, count=1)
    lines = cleaned.splitlines()
    # Keep the requested version when the model returns an editor-style
    # "original/shorter version" wrapper; discard the wrapper and its notes.
    shorter = next((i for i, line in enumerate(lines) if re.match(r"^\s*(?:\*\*|__)?krótsza wersja", line, re.I)), None)
    if shorter is not None:
        lines = lines[shorter + 1:]
    notes = next((i for i, line in enumerate(lines) if re.match(r"^\s*(?:\*\*|__)?(?:uwagi(?:\s+redakcyjne)?|edytor)(?:\s*\([^)]*\))?\s*:\s*(?:\*\*|__)?", line, re.I)), None)
    if notes is not None:
        lines = lines[:notes] if notes > 0 else lines
    lines = [line for line in lines if not META_TRAILER.match(line) and not META_LABEL.match(line)]
    lines = [line for line in lines if line.strip() not in {"---", "***"}]
    lines = [line for line in lines if not re.match(r"^\s*\(Jeśli chcesz .*\)\s*$", line, re.I)]
    lines = [re.sub(r"\s*[–—-]\s*\*?\(?\s*redakcja:.*?\)?\*?\s*$", "", line, flags=re.I) for line in lines]
    while lines and not lines[0].strip():
        lines.pop(0)
    result = "\n".join(lines).strip()
    if not result:
        return RenderResult(text="", metadata_detected=True, cleaned=True, confidence=0.88,
                            warning="Odpowiedź zawierała wyłącznie metakomentarz; wynik wymaga ponowienia generacji.")
    return RenderResult(text=result, metadata_detected=True, cleaned=result != original, confidence=0.91)
