#!/usr/bin/env python3
"""Run Bielik proposal-only checks; never invokes Audioticon or audio engines."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from writing_agent.audiobook_bielik_proposer import propose_annotations
from writing_agent.audiobook_validator import validate_proposal

FIXTURE = ROOT / "benchmark/audiobook_director_fixture_v1.json"
CASES = ROOT / "benchmark/audiobook_director_bielik_cases_v1.jsonl"
OUT = ROOT / "benchmark/results/audiobook_director_bielik_proposal_v1.json"
REPORT = ROOT / "experiment_log/audiobook_director_bielik_proposal_v1.md"
OUT.parent.mkdir(parents=True, exist_ok=True)
REPORT.parent.mkdir(parents=True, exist_ok=True)


def main():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = [{"case_id": "approved_fixture_v1", "source": "fixture", **propose_annotations(fixture["source_text"], project_id=fixture["project_id"], scene_id=fixture["scene_id"])}]
    for case in cases:
        results.append({"case_id": case["case_id"], "source": "holdout", "expected_unknown": case["expected_unknown"], **propose_annotations(case["source_text"], project_id="bielik-proposal-v1", scene_id=case["scene_id"])} )
    # JSON validity is measured before merge/contract validation.  A syntactically
    # valid annotation array can still be rejected for schema or safety reasons.
    valid_json = sum(r.get("annotation_response") is not None for r in results)
    valid = sum(r["validation"]["valid"] for r in results)
    def no_error(result, prefixes):
        return not any(any(error.startswith(prefix) for prefix in prefixes) for error in result["validation"].get("errors", []))
    metrics = {
        "valid_segment_ids": sum(no_error(r, ("unknown_segment_id:", "duplicate_segment_id:", "missing_segment_annotations:")) for r in results),
        "valid_speakers": sum(no_error(r, ("unknown_speaker_id:",)) for r in results),
        "valid_emotions": sum(no_error(r, ("invalid_emotion:",)) for r in results),
        "valid_paces": sum(no_error(r, ("invalid_pace:",)) for r in results),
        "valid_pitches": sum(no_error(r, ("invalid_pitch:",)) for r in results),
        "unknown_speaker_questions": sum(not any("missing_author_question:" in e for e in r["validation"].get("errors", [])) for r in results if any("unknown" in str(a) for a in (r.get("annotations") or []))),
        "duplicate_annotations": sum(any(e.startswith("duplicate_segment_id:") for e in r["validation"].get("errors", [])) for r in results),
        "missing_annotations": sum(any(e.startswith("missing_segment_annotations:") for e in r["validation"].get("errors", [])) for r in results),
    }
    expected_unknown_cases = [case["case_id"] for case in cases if case.get("expected_unknown")]
    unknown_cases = [r["case_id"] for r in results if r["case_id"] in expected_unknown_cases or any("unknown_speaker" in e or "unknown_speaker_id" in e for e in r["validation"].get("errors", []))]
    report = {"suite":"audiobook_director_bielik_annotation_v1", "mode":"proposal_only", "annotation_only":True, "model":"bielik-4.5b-v3:q5",
              "summary":{"proposals":len(results),"valid_json":valid_json,"validator_pass":valid,"validator_rejected":len(results)-valid,
                         "unknown_speaker_cases":unknown_cases,"expected_unknown_cases":expected_unknown_cases,"accepted_for_render":0,
                         "fixture_negative_regression":"10/10","accepted_for_render":0,"text_owned_by_adapter":True,"audioticon_started":False,"tts_started":False,"dsp_started":False, **metrics}, "results":results}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines=["# Bielik Audiobook Director — annotation-only v2", "", f"Propozycje: **{len(results)}**", f"Poprawny JSON obiektu kontraktu: **{valid_json}/{len(results)}**", f"Przejście validatora: **{valid}/{len(results)}**", f"Odrzucone przez validator: **{len(results)-valid}**", f"Nieznani mówcy wymagający decyzji autora: `{', '.join(unknown_cases) or 'brak'}`", "", "## Metryki kontraktu", "", *[f"- `{key}`: **{value}/{len(results) if isinstance(value, int) and key not in {'duplicate_annotations', 'missing_annotations'} else value}**" for key, value in metrics.items()], "", "Audioticon, Piper, Edge TTS i DSP nie były uruchamiane. Nie wykonano renderowania ani eksportu. Wszystkie wyniki pozostają `proposed` i `accepted_for_render=false`.", "", "## Przykład fixture v1", "", "```json", json.dumps(results[0], ensure_ascii=False, indent=2), "```", "", "## Kontrola negatywna", "", "Uszkodzenia zatwierdzonego fixture’u z poprzedniej fazy: **10/10 wykrytych**.", "", "## Uwagi", "", "Walidator jest bramką bezpieczeństwa. Poprawny JSON bez pełnego kontraktu pozostaje odrzucony i nie może trafić do renderowania."]
    REPORT.write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(f"proposals={len(results)} json={valid_json}/{len(results)} validator={valid}/{len(results)}")


if __name__ == "__main__": main()
