#!/usr/bin/env python3
"""Evaluate Bielik only on its intended audiobook-director specialization."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from writing_agent.audiobook_annotations import expected_speaker, segment_source
from writing_agent.audiobook_bielik_proposer import propose_annotations

CASES = ROOT / "benchmark/audiobook_director_specialization_cases_v1.jsonl"
OUT = ROOT / "benchmark/results/audiobook_director_specialization_v1.json"
REPORT = ROOT / "experiment_log/audiobook_director_specialization_v1.md"
OUT.parent.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    cached = {}
    if OUT.exists():
        try:
            cached = {item["case_id"]: item for item in json.loads(OUT.read_text(encoding="utf-8")).get("results", [])}
        except (json.JSONDecodeError, KeyError):
            cached = {}
    for case in cases:
        old = cached.get(case["case_id"])
        result = old or propose_annotations(case["source_text"], project_id="bielik-specialization-v1", scene_id=case["case_id"])
        proposal = result.get("proposal")
        predicted = [item.get("speaker") for item in (proposal or {}).get("segments", [])]
        expected_segments = [expected_speaker(item["text"]) for item in segment_source(case["source_text"])]
        speaker_match_count = sum(a == b for a, b in zip(predicted, expected_segments))
        speaker_match = len(predicted) == len(expected_segments) and speaker_match_count == len(expected_segments)
        results.append({"case_id": case["case_id"], "family": case["family"], "expected_speaker": case["expected_speaker"],
                        "target": case.get("target"), "valid": result["validation"]["valid"],
                        "speaker_match": speaker_match, "speaker_match_count": speaker_match_count, "speaker_expected_count": len(expected_segments), "text_preserved": '"text"' not in result.get("raw_response", ""),
                        "predicted_speaker": predicted, "expected_segment_speakers": expected_segments, "validation": result["validation"],
                        "raw_response": result.get("raw_response", ""), "proposal": proposal,
                        "accepted_for_render": False})
    by_family = {}
    for family in sorted({item["family"] for item in results}):
        group = [item for item in results if item["family"] == family]
        by_family[family] = {"count": len(group), "valid": sum(x["valid"] for x in group),
                             "speaker_assignment": sum(x["speaker_match_count"] for x in group),
                             "speaker_total": sum(x["speaker_expected_count"] for x in group),
                             "text_preserved": sum(x["text_preserved"] for x in group)}
    summary = {"cases": len(results), "valid_json": sum(bool(x["raw_response"]) for x in results),
               "validator_pass": sum(x["valid"] for x in results),
               "emotion_score": "manual_review_required", "pause_score": "manual_review_required",
               "pace_score": "manual_review_required", "narrator_assignment_score": sum(x["speaker_match_count"] for x in results if x["expected_speaker"] == "narrator"),
               "narrator_assignment_total": sum(x["speaker_expected_count"] for x in results if x["expected_speaker"] == "narrator"),
               "speaker_assignment_score": sum(x["speaker_match_count"] for x in results),
               "text_preservation": sum(x["text_preserved"] for x in results),
               "manual_correction_rate": "manual_review_required", "accepted_for_render": 0,
               "audioticon_started": False, "tts_started": False, "dsp_started": False, "by_family": by_family}
    payload = {"suite": "audiobook_director_specialization_v1", "model": "bielik-4.5b-v3:q5", "summary": summary, "results": results}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    total_segments = sum(x["speaker_expected_count"] for x in results)
    lines = ["# Bielik — holdout specjalizacyjny Audiobook Director v1", "", f"Przypadki: **{len(results)}**", f"Validator: **{summary['validator_pass']}/{len(results)}**", f"Zachowanie tekstu przez adapter: **{summary['text_preservation']}/{len(results)}**", f"Dopasowanie mówcy segment po segmencie: **{summary['speaker_assignment_score']}/{total_segments}**", "", "## Wyniki rodzin", "", "| Rodzina | N | Validator | Speaker | Tekst |", "|---|---:|---:|---:|---:|"]
    for family, values in by_family.items():
        lines.append(f"| {family} | {values['count']} | {values['valid']} | {values['speaker_assignment']}/{values['speaker_total']} | {values['text_preserved']} |")
    lines += ["", "Ocena emocji, pauz i tempa wymaga osobnej ręcznej rubryki; runner nie udaje oceny artystycznej.", "", "Audioticon, Piper, Edge TTS i DSP nie były uruchamiane. Wszystkie wyniki pozostają `proposed`; `accepted_for_render=0`."]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"specialization cases={len(results)} validator={summary['validator_pass']}/{len(results)} speaker={summary['speaker_assignment_score']}/{total_segments}")


if __name__ == "__main__":
    main()
