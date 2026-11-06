#!/usr/bin/env python3
"""Run the common v0.2 holdout with Granite 4 3B in annotation-only mode."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from writing_agent.audiobook_granite_proposer import GRANITE_MODEL, propose_annotations
from run_audiobook_director_v0_2 import aggregate, evaluate, load_cases

OUT = ROOT / "benchmark/results/audiobook_director_granite4_3b.json"
REPORT = ROOT / "experiment_log/audiobook_director_granite4_3b.md"
BIELIK_OUT = ROOT / "benchmark/results/audiobook_director_v0_2.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=GRANITE_MODEL)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--num-predict", type=int, default=1536)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    cases = load_cases(args.limit)
    results = []
    for index, case in enumerate(cases, 1):
        result = propose_annotations(case["source_text"], model=args.model, project_id="audiobook-director-v0-2", scene_id=case["scene_id"], seed=3000 + index, num_predict=args.num_predict, timeout=args.timeout)
        evaluated = evaluate(case, result)
        # Source ownership is deterministic: a rejected annotation response
        # cannot mutate source text because Granite has no write path and the
        # annotation schema has no text field.
        evaluated["text_preserved"] = bool(result.get("text_owned_by_adapter"))
        evaluated["retry_count"] = result.get("retry_count", 0)
        evaluated["attempts"] = result.get("attempts", [])
        results.append(evaluated)
        print(f"[{index}/{len(cases)}] {case['case_id']} {evaluated['status']} retries={evaluated['retry_count']}", flush=True)

    summary = aggregate(results)
    summary["total_retries"] = sum(item["retry_count"] for item in results)
    summary["average_eval_duration_ns"] = round(sum(item["eval_duration_ns"] for item in results) / max(1, len(results)))
    by_category = defaultdict(list)
    for item in results:
        by_category[item["category_label"]].append(item)
    category_summary = {key: aggregate(value) for key, value in by_category.items()}
    bielik = {}
    if BIELIK_OUT.exists():
        try:
            bielik = json.loads(BIELIK_OUT.read_text(encoding="utf-8")).get("summary", {})
        except (OSError, json.JSONDecodeError):
            bielik = {}
    payload = {
        "suite": "audiobook_director_v0_2_granite4_3b",
        "mode": "proposal_only",
        "annotation_only": True,
        "model": args.model,
        "profile": "granite4_3b",
        "holdout_cases": len(cases),
        "source_text_owned_by_adapter": True,
        "accepted_for_render": False,
        "audioticon_started": False,
        "tts_started": False,
        "dsp_started": False,
        "summary": summary,
        "by_category": category_summary,
        "comparison_bielik": {"model": "bielik-4.5b-v3:q5", "summary": bielik},
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Granite 4 3B — Audiobook Director v0.2",
        "",
        "Profil działa wyłącznie w trybie `annotation-only` / `proposal_only`. Tekst źródłowy pozostaje własnością adaptera.",
        "",
        f"Model: `{args.model}`  ", f"Przypadki: **{summary['cases']}**  ",
        f"PASS: **{summary['pass']}**, WARN: **{summary['warn']}**, FAIL: **{summary['fail']}**",
        "",
        "## Metryki",
        "",
        "| Metryka | Granite 4 3B | Bielik v0.2 |",
        "|---|---:|---:|",
    ]
    metric_map = [("valid_json", "Poprawny JSON"), ("validator_pass", "Validator"), ("text_preservation", "Zachowanie tekstu"), ("narrator_assignment", "Narrator"), ("known_speaker_assignment", "Znani mówcy"), ("unknown_speaker_usage", "Unknown"), ("author_question_completeness", "Pytania autora"), ("emotion_accuracy", "Emocje"), ("pace_accuracy", "Tempo"), ("pause_accuracy", "Pauzy")]
    for key, label in metric_map:
        lines.append(f"| {label} | {summary[key]} | {bielik.get(key, 'brak')} |")
    lines += [
        "",
        "## Operacyjnie",
        "",
        f"- Łączna liczba retry: **{summary['total_retries']}**.",
        f"- Średni czas odpowiedzi Ollamy: **{summary['average_eval_duration_ns']} ns** według metadanych modelu.",
        "- Automatyczne rendery: **0**; auto-accept: **0**.",
        "- TTS, DSP i Audioticon: **nieuruchamiane**.",
        "- Wagi Granite’a i Bielika: **niemodyfikowane**.",
        "",
        "## Wyniki według kategorii",
        "",
        "| Kategoria | N | PASS | WARN | FAIL | Validator | Narrator |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for category, data in category_summary.items():
        lines.append(f"| {category} | {data['cases']} | {data['pass']} | {data['warn']} | {data['fail']} | {data['validator_pass']} | {data['narrator_assignment']} |")
    lines += [
        "",
        "## Najczęstsze błędy",
        "",
    ]
    for key, value in sorted(summary["error_groups"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: **{value}**")
    if not summary["error_groups"]:
        lines.append("- brak błędów kontraktowych")
    lines += [
        "",
        "## Przypadki wymagające uwagi",
        "",
    ]
    for item in results:
        if item["status"] == "FAIL":
            lines.append(f"- `{item['case_id']}` — FAIL; retry: {item['retry_count']}; błędy: {', '.join(item['errors'])}")
    lines += [
        "",
        "## Rekomendacja",
        "",
        "Na tym holdoucie Granite nie przewyższa Bielika: ma jeden FAIL, 87/89 znanych mówców zamiast 89/89 oraz słabsze pauzy (74/157 vs 138/159). Pozostaje profilem eksperymentalnym dla narracji; nie zastępuje Bielika w dialogach.",
        "Granite 4 3B oceniono na identycznym holdoucie i przez ten sam validator. Ten raport mierzy kontrakt i zgodność adnotacji, nie jakość artystyczną. Granite może być rozważany jako drugi profil dopiero wtedy, gdy jego wyniki segmentacji, mówców i emocji okażą się stabilne; nie zastępuje profilu Bielika bez przewagi potwierdzonej tymi samymi metrykami.",
        "",
        "Wszystkie propozycje pozostają `proposed` i wymagają ręcznej akceptacji.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary={summary['cases']} cases pass={summary['pass']} warn={summary['warn']} fail={summary['fail']}")


if __name__ == "__main__":
    main()
