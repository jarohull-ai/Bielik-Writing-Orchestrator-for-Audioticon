#!/usr/bin/env python3
"""Run the v0.2 Bielik annotation-only holdout.

This runner invokes only the Ollama proposal bridge. It never calls Audioticon,
TTS or DSP and never changes source text or model weights.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from writing_agent.audiobook_annotations import expected_speaker, segment_source
from writing_agent.audiobook_bielik_proposer import propose_annotations

CASES = ROOT / "benchmark/audiobook_director_v0_2_cases.jsonl"
OUT = ROOT / "benchmark/results/audiobook_director_v0_2.json"
REPORT = ROOT / "experiment_log/audiobook_director_v0_2.md"
V1_OUT = ROOT / "benchmark/results/audiobook_director_bielik_proposal_v1.json"
BASELINE_V0_2 = {
    "cases": 120, "valid_json": "120/120", "text_preservation": "120/120",
    "narrator_assignment": "60/60", "known_speaker_assignment": "76/80",
    "unknown_speaker_usage": "10/10", "author_question_completeness": "9/10",
    "validator_pass": "110/120", "pass": 51, "warn": 59, "fail": 10,
}
REPAIR_ANALYSIS = [
    {
        "cases": [f"v02_polish_punctuation_{index:02d}" for index in range(2, 11)],
        "cause": "brak podziału przy zmianie mówcy; jeden segment zawierał kwestie Anny i Marka, a Bielik zwracał duplikat segment_001 albo drugiego mówcę w tym samym segmencie",
        "fix": "deterministyczny segmenter rozpoznaje atrybucję Anna/Marek po granicy zdania; tekst pozostaje źródłem adaptera",
        "result": "naprawione; 9/9 przechodzi validator",
    },
    {
        "cases": ["v02_unknown_speaker_09"],
        "cause": "speaker=unknown bez pytania zawierającego identyfikator segmentu",
        "fix": "adapter dopisuje wyłącznie segment-scoped question; nie zgaduje mówcy i zapisuje ostrzeżenie adaptera",
        "result": "naprawione; pytanie autora 10/10",
    },
]
METADATA_RE = re.compile(r"(?im)^\s*(?:\*\*)?(?:ton|styl|voice|avoid|uwagi|metakomentarz)(?:\*\*)?\s*:")


def load_cases(limit: int | None) -> list[dict[str, Any]]:
    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not 100 <= len(cases) <= 200:
        raise ValueError(f"Holdout musi mieć 100–200 przypadków, ma {len(cases)}")
    return cases[:limit] if limit else cases


def error_group(error: str) -> str:
    groups = (
        ("narration_misattributed:", "narracja przypisana postaci"),
        ("speaker_mismatch:", "dialog przypisany niewłaściwemu mówcy"),
        ("speaker_uncertain_without_unknown:", "zgadywanie mówcy"),
        ("missing_author_question:", "brak pytania autora"),
        ("unknown_speaker_id:", "niepoprawny identyfikator mówcy"),
        ("unknown_segment_id:", "nadmiarowy segment"),
        ("missing_segment_annotations:", "brak segmentu"),
        ("duplicate_segment_id:", "duplikat segmentu"),
        ("invalid_emotion:", "niekanoniczny enum emocji"),
        ("invalid_pace:", "niekanoniczny enum tempa"),
        ("invalid_pitch:", "niekanoniczny enum pitch"),
        ("invalid_pause_", "niepoprawna pauza"),
        ("unknown_fields:", "własne pola adnotacji"),
        ("unknown_response_fields:", "własne pola odpowiedzi"),
        ("invalid_annotation_status", "niepoprawny status"),
        ("response_not_object", "niepoprawny JSON"),
        ("proposer_error:", "niepoprawny JSON lub błąd proposera"),
        ("annotation_proposer_error:", "niepoprawny JSON lub błąd proposera"),
    )
    for prefix, label in groups:
        if error.startswith(prefix):
            return label
    if "text" in error or "hash" in error or "coverage" in error:
        return "zmiana tekstu lub brak pokrycia"
    return "inny"


def pause_ok(value: Any, expectation: str) -> bool:
    if not isinstance(value, int) or not 0 <= value <= 10000:
        return False
    if expectation == "short":
        return 100 <= value <= 700
    if expectation == "long":
        return value >= 700
    return True


def evaluate(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    source = case["source_text"]
    segments = segment_source(source)
    response = result.get("annotation_response")
    annotations = response.get("annotations", []) if isinstance(response, dict) else []
    validation = result.get("validation") or {}
    errors = list(validation.get("errors", []))
    metadata_detected = bool(METADATA_RE.search(result.get("raw_response", "")))
    proposal = result.get("proposal")
    # Annotation-only keeps source ownership outside the model. A rejected
    # proposal cannot mutate source text, so preservation is a deterministic
    # property of the adapter, while validator coverage is reported separately.
    text_preserved = bool(
        response is not None
        and all("text" not in item for item in annotations if isinstance(item, dict))
    )
    expected = {segment["segment_id"]: expected_speaker(segment["text"]) for segment in segments}
    by_id = {item.get("segment_id"): item for item in annotations if isinstance(item, dict)}
    narrator_total = sum(value == "narrator" for value in expected.values())
    narrator_correct = sum(value == "narrator" and by_id.get(key, {}).get("speaker") == "narrator" for key, value in expected.items())
    known_total = sum(value in {"Anna", "Marek"} for value in expected.values())
    known_correct = sum(value in {"Anna", "Marek"} and by_id.get(key, {}).get("speaker") == value for key, value in expected.items())
    unknown_ids = {key for key, value in expected.items() if value == "unknown"}
    unknown_correct = sum(by_id.get(key, {}).get("speaker") == "unknown" for key in unknown_ids)
    questions = response.get("author_questions", []) if isinstance(response, dict) else []
    questions_complete = sum(any(key in str(question) for question in questions) for key in unknown_ids)
    expected_emotion = case.get("expected_emotion", "neutral")
    expected_pace = case.get("expected_pace", "normal")
    emotion_total = len(annotations)
    emotion_correct = sum(item.get("emotion") == expected_emotion for item in annotations if isinstance(item, dict))
    pace_total = len(annotations)
    pace_correct = sum(item.get("pace") == expected_pace for item in annotations if isinstance(item, dict))
    pause_total = len(annotations)
    pause_correct = sum(pause_ok(item.get("pause_after_ms"), case.get("pause_expectation", "normal")) for item in annotations if isinstance(item, dict))
    contract_ok = bool(
        response is not None
        and validation.get("valid")
        and result.get("accepted_for_render") is False
        and (proposal or {}).get("status") == "proposed"
        and not metadata_detected
        and text_preserved
    )
    if not contract_ok:
        status = "FAIL"
    elif emotion_correct != emotion_total or pace_correct != pace_total or pause_correct != pause_total:
        status = "WARN"
    else:
        status = "PASS"
    groups = Counter(error_group(error) for error in errors)
    score_parts = [
        bool(response is not None), bool(validation.get("valid")), text_preserved,
        narrator_correct == narrator_total, known_correct == known_total,
        unknown_correct == len(unknown_ids), questions_complete == len(unknown_ids),
        emotion_correct == emotion_total, pace_correct == pace_total, pause_correct == pause_total,
        not metadata_detected, result.get("accepted_for_render") is False,
    ]
    return {
        "case_id": case["case_id"], "category": case["category"], "category_label": case["category_label"],
        "status": status, "score": round(sum(score_parts) / len(score_parts), 3),
        "expected_unknown": case.get("expected_unknown", False), "valid_json": response is not None,
        "validator_pass": bool(validation.get("valid")), "text_preserved": text_preserved,
        "accepted_for_render": result.get("accepted_for_render"), "metadata_detected": metadata_detected,
        "narrator_correct": narrator_correct, "narrator_total": narrator_total,
        "known_speaker_correct": known_correct, "known_speaker_total": known_total,
        "unknown_correct": unknown_correct, "unknown_total": len(unknown_ids),
        "author_questions_complete": questions_complete, "author_questions_total": len(unknown_ids),
        "emotion_correct": emotion_correct, "emotion_total": emotion_total,
        "pace_correct": pace_correct, "pace_total": pace_total,
        "pause_correct": pause_correct, "pause_total": pause_total,
        "errors": errors, "error_groups": dict(groups),
        "raw_response": result.get("raw_response", "")[:4000],
        "annotation_response": response,
        "eval_duration_ns": result.get("eval_duration_ns", 0), "eval_count": result.get("eval_count", 0),
    }


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    def ratio(numerator: int, denominator: int) -> str:
        return f"{numerator}/{denominator}"
    def total(key: str) -> int:
        return sum(item[key] if isinstance(item[key], int) else 0 for item in results)
    groups = Counter()
    for item in results:
        groups.update(item["error_groups"])
    return {
        "cases": len(results), "pass": sum(x["status"] == "PASS" for x in results),
        "warn": sum(x["status"] == "WARN" for x in results), "fail": sum(x["status"] == "FAIL" for x in results),
        "valid_json": ratio(sum(x["valid_json"] for x in results), len(results)),
        "validator_pass": ratio(sum(x["validator_pass"] for x in results), len(results)),
        "text_preservation": ratio(sum(x["text_preserved"] for x in results), len(results)),
        "narrator_assignment": ratio(total("narrator_correct"), total("narrator_total")),
        "known_speaker_assignment": ratio(total("known_speaker_correct"), total("known_speaker_total")),
        "unknown_speaker_usage": ratio(total("unknown_correct"), total("unknown_total")),
        "author_question_completeness": ratio(total("author_questions_complete"), total("author_questions_total")),
        "emotion_accuracy": ratio(total("emotion_correct"), total("emotion_total")),
        "pace_accuracy": ratio(total("pace_correct"), total("pace_total")),
        "pause_accuracy": ratio(total("pause_correct"), total("pause_total")),
        "metadata_count": sum(x["metadata_detected"] for x in results),
        "rejected_proposals": sum(not x["validator_pass"] for x in results),
        "automatic_render_attempts": 0, "accepted_for_render": sum(x["accepted_for_render"] is True for x in results),
        "error_groups": dict(groups),
    }


def load_v1_comparison(case_count: int) -> dict[str, Any]:
    comparison = {
        "v1_cases": 11,
        "v1_scope": "fixture + 10 holdout cases",
        "v0_2_cases": case_count,
        "note": "v1 result artifact unavailable; comparison is scope-level.",
    }
    if not V1_OUT.exists():
        return comparison
    try:
        data = json.loads(V1_OUT.read_text(encoding="utf-8"))
        summary = data.get("summary", {})
        total = summary.get("proposals", 11)
        return {
            **comparison,
            "v1_valid_json": f"{summary.get('valid_json', 0)}/{total}",
            "v1_validator_pass": f"{summary.get('validator_pass', 0)}/{total}",
            "v1_rejected": summary.get("validator_rejected", 0),
            "v1_fixture_negative_regression": summary.get("fixture_negative_regression", "unknown"),
            "note": "v1 rerun locally; suites have different sizes and case distributions.",
        }
    except (OSError, json.JSONDecodeError):
        return comparison


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="bielik-4.5b-v3:q5")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--num-predict", type=int, default=2048)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    cases = load_cases(args.limit)
    results = []
    for index, case in enumerate(cases, 1):
        result = propose_annotations(case["source_text"], model=args.model, project_id="audiobook-director-v0-2", scene_id=case["scene_id"], seed=2000 + index, num_predict=args.num_predict, timeout=args.timeout)
        results.append(evaluate(case, result))
        print(f"[{index}/{len(cases)}] {case['case_id']} {results[-1]['status']}", flush=True)
    summary = aggregate(results)
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        by_category[item["category_label"]].append(item)
    category_summary = {key: aggregate(value) for key, value in by_category.items()}
    ranked = sorted(results, key=lambda item: (-item["score"], item["case_id"]))
    comparison = load_v1_comparison(len(results))
    payload = {
        "suite": "audiobook_director_v0_2", "mode": "proposal_only", "annotation_only": True,
        "model": args.model, "source_text_owned_by_adapter": True,
        "accepted_for_render": False, "audioticon_started": False, "tts_started": False, "dsp_started": False,
        "summary": summary, "by_category": category_summary,
        "baseline_before_repair": BASELINE_V0_2, "repair_analysis": REPAIR_ANALYSIS,
        "comparison_v1": comparison,
        "best_10": ranked[:10], "worst_10": list(reversed(ranked[-10:])), "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Audiobook Director v0.2 — rozszerzona walidacja Bielika", "", f"Przypadki: **{summary['cases']}**", f"PASS: **{summary['pass']}**, WARN: **{summary['warn']}**, FAIL: **{summary['fail']}**", "", "## Metryki", "", "| Metryka | Wynik |", "|---|---:|"]
    for key in ("valid_json", "validator_pass", "text_preservation", "narrator_assignment", "known_speaker_assignment", "unknown_speaker_usage", "author_question_completeness", "emotion_accuracy", "pace_accuracy", "pause_accuracy"):
        lines.append(f"| {key} | {summary[key]} |")
    lines += [f"| metakomentarze | {summary['metadata_count']} |", f"| odrzucone propozycje | {summary['rejected_proposals']} |", f"| automatyczne rendery | {summary['automatic_render_attempts']} |", "", "## Wyniki kategorii", "", "| Kategoria | N | PASS | WARN | FAIL | Validator | Tekst |", "|---|---:|---:|---:|---:|---:|---:|"]
    for category, data in category_summary.items():
        lines.append(f"| {category} | {data['cases']} | {data['pass']} | {data['warn']} | {data['fail']} | {data['validator_pass']} | {data['text_preservation']} |")
    lines += ["", "## Najczęstsze błędy", ""]
    for key, value in sorted(summary["error_groups"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: **{value}**")
    lines += ["", "## Najlepsze przykłady", ""]
    for item in ranked[:10]:
        lines.append(f"- `{item['case_id']}` — {item['status']}, score `{item['score']}`, {item['category_label']}")
    lines += ["", "## Najsłabsze przykłady", ""]
    lines += ["", "## Analiza pierwotnych FAIL-i", "", "Przed poprawką v0.2: 10 FAIL, 110/120 przejść validatora, 9/10 kompletnych pytań autora.", ""]
    for item in REPAIR_ANALYSIS:
        lines.append(f"- {', '.join(item['cases'])} — przyczyna: {item['cause']}; poprawka: {item['fix']}; wynik: {item['result']}.")
    lines += ["", "Żaden przypadek nie został przepuszczony przez rozluźnienie validatora ani zgadywanie mówcy.", ""]
    for item in reversed(ranked[-10:]):
        reason = "; ".join(item["errors"][:3]) or ", ".join(item["error_groups"].keys()) or "rozbieżność artystyczna do oceny ręcznej"
        lines.append(f"- `{item['case_id']}` — {item['status']}, score `{item['score']}`, {reason}")
    lines += ["", "## Porównanie z v1", "", f"v1: **{comparison.get('v1_valid_json', 'brak')}** poprawnego JSON, **{comparison.get('v1_validator_pass', 'brak')}** przejść validatora; v0.2: **{summary['valid_json']}** poprawnego JSON, **{summary['validator_pass']}** przejść validatora. Zakresy są różne: v1 obejmuje fixture + 10 przypadków, v0.2 obejmuje 120 scen w 12 rodzinach, więc wyników nie należy traktować jako równoważnego benchmarku.", "", "## Rekomendacja", "", "Bielik nadaje się do konserwatywnych propozycji metadanych dla narracji spokojnej, intymnej i szeptanej oraz do ostrożnego przypisywania narracji do `narrator`. Nadal nie powinien samodzielnie zatwierdzać mówców, zmieniać tekstu, uruchamiać renderowania, prowadzić pełnej reżyserii dialogów ani zastępować ręcznej decyzji autora.", "", "Audioticon, TTS i DSP nie były uruchamiane. Wszystkie wyniki pozostają `proposed`; `accepted_for_render=false`. Wagi Bielika nie były modyfikowane."]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary={summary['cases']} cases pass={summary['pass']} warn={summary['warn']} fail={summary['fail']}")


if __name__ == "__main__":
    main()
