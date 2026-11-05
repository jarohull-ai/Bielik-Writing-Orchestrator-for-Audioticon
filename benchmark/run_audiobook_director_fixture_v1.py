#!/usr/bin/env python3
"""Validate the approved audiobook fixture without invoking Audioticon, TTS or Bielik."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from writing_agent.audiobook_validator import validate_proposal
from writing_agent.audioticon_adapter import export_audioticon_script

FIXTURE = ROOT / "benchmark/audiobook_director_fixture_v1.json"
NEGATIVE = ROOT / "benchmark/audiobook_director_fixture_negative_v1.jsonl"
OUT = ROOT / "benchmark/results/audiobook_director_fixture_v1.json"
REPORT = ROOT / "experiment_log/audiobook_director_fixture_v1.md"
OUT.parent.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)


def mutate(proposal, case):
    p = copy.deepcopy(proposal)
    mutation = case["mutation"]
    if mutation == "remove_segment": p["segments"].pop(2)
    elif mutation == "replace_text":
        for s in p["segments"]: s["text"] = s["text"].replace(case["from"], case["to"])
    elif mutation == "swap_segments": p["segments"][0], p["segments"][1] = p["segments"][1], p["segments"][0]
    elif mutation == "bad_hash": p["source_text_hash"] = "0" * 64
    elif mutation == "bad_speaker_id": p["segments"][4]["speaker"] = "ghost"
    elif mutation == "bad_preset": p["segments"][2]["sound_cues"][0]["name"] = "unknown:missing"
    elif mutation == "approved_status": p["status"] = "approved"
    elif mutation == "extra_text": p["segments"][1]["text"] += " Dopisano."
    elif mutation == "remove_author_question": p["open_questions"] = []
    return p


def main():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    source = fixture["source_text"]
    positive = validate_proposal(fixture["proposal"], source)
    exported = export_audioticon_script(fixture["proposal"], source) if positive["valid"] else None
    negative = []
    for line in NEGATIVE.read_text(encoding="utf-8").splitlines():
        case = json.loads(line)
        result = validate_proposal(mutate(fixture["proposal"], case), source)
        detected = all(error in result["errors"] for error in case["expected_errors"])
        negative.append({**case, "valid": result["valid"], "errors": result["errors"], "detected": detected})
    report = {
        "fixture_id": fixture["fixture_id"],
        "positive": {"valid": positive["valid"], "errors": positive["errors"], "warnings": positive["warnings"], "exported_script": exported},
        "negative": negative,
        "summary": {"positive_pass": positive["valid"], "negative_pass": sum(x["detected"] for x in negative), "negative_total": len(negative), "tts_started": False, "dsp_started": False, "audioticon_started": False, "bielik_used": False},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Audiobook Director — ręcznie zatwierdzony fixture v1", "", "Pozytywny fixture: **PASS**" if positive["valid"] else "Pozytywny fixture: **FAIL**", f"Przypadki negatywne: **{sum(x['detected'] for x in negative)}/{len(negative)}**", "", "Audioticon, TTS, DSP i Bielik nie były uruchamiane. Repozytorium Audioticonu nie było modyfikowane. Wagi Bielika nie były używane ani zmieniane.", "", "## Źródłowy tekst", "", "```text", source, "```", "", "## Ręcznie zatwierdzony JSON", "", "```json", json.dumps(fixture["proposal"], ensure_ascii=False, indent=2), "```", "", "## Decyzje negatywne", ""]
    for item in negative: lines.append(f"- `{item['case_id']}`: {'PASS — odrzucono' if item['detected'] else 'FAIL'}; `{', '.join(item['errors'])}`")
    lines += ["", "## Eksport adaptera", "", "```text", exported or "brak — walidacja pozytywna nie przeszła", "```", "", "Fixture ma status `approved_fixture`, który oznacza zatwierdzenie danych testowych przez człowieka. Status `approved` pozostaje zabroniony dla wyniku modelu."]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"positive={'PASS' if positive['valid'] else 'FAIL'} negative={sum(x['detected'] for x in negative)}/{len(negative)}")


if __name__ == "__main__": main()
