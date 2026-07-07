import json
import os
import sys
import time
from pathlib import Path
from collections import Counter

import requests


EVAL_FILE = Path(__file__).resolve().parent / "eval" / "bugs.json"
TRIAGE_URL = os.getenv("TRIAGE_URL", "http://localhost:8000/triage")
REQUEST_TIMEOUT = int(os.getenv("EVAL_REQUEST_TIMEOUT", "300"))
SLEEP_SECONDS = float(os.getenv("EVAL_SLEEP_SECONDS", "10"))
SEVERITY_ORDER = ["low", "medium", "high", "critical"]


def _payload_from_bug(bug: dict) -> dict:
    return {
        "bug_id": bug.get("id"),
        "title": bug["title"][:200],
        "description": bug["description"][:2500],
        "repository": bug.get("repo"),
        "issue_url": bug.get("url"),
        "labels": bug.get("labels", []),
    }


def _backend_is_up() -> bool:
    try:
        health_url = TRIAGE_URL.rsplit("/", 1)[0] + "/health"
        resp = requests.get(health_url, timeout=5)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def compute_report(results: list[dict]) -> dict:
    confusion = {t: {p: 0 for p in SEVERITY_ORDER} for t in SEVERITY_ORDER}
    for r in results:
        if r["predicted"] in SEVERITY_ORDER and r["truth"] in SEVERITY_ORDER:
            confusion[r["truth"]][r["predicted"]] += 1

    per_class = {}
    for label in SEVERITY_ORDER:
        tp = confusion[label][label]
        fp = sum(confusion[t][label] for t in SEVERITY_ORDER if t != label)
        fn = sum(confusion[label][p] for p in SEVERITY_ORDER if p != label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(confusion[label].values()),
        }

    total = sum(sum(row.values()) for row in confusion.values())
    accuracy = sum(confusion[l][l] for l in SEVERITY_ORDER) / total if total else 0.0
    macro_f1 = sum(c["f1"] for c in per_class.values()) / len(SEVERITY_ORDER)

    truths = [r["truth"] for r in results if r["truth"] in SEVERITY_ORDER]
    majority_label, majority_count = Counter(truths).most_common(1)[0]
    majority_baseline = majority_count / len(truths) if truths else 0.0

    # Count fallbacks
    total_fallbacks = sum(r.get("fallback_calls", 0) for r in results)

    return {
        "confusion": confusion,
        "per_class": per_class,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "majority_baseline": majority_baseline,
        "majority_label": majority_label,
        "total_fallbacks": total_fallbacks,
    }


def print_report(report: dict):
    print("\nConfusion matrix (rows=truth, cols=predicted):")
    print(" " * 12 + "".join(f"{l:>10}" for l in SEVERITY_ORDER))
    for t in SEVERITY_ORDER:
        print(f"{t:>12}" + "".join(f"{report['confusion'][t][p]:>10}" for p in SEVERITY_ORDER))

    print("\nPer-class metrics:")
    for label, m in report["per_class"].items():
        print(f"  {label:10s} precision={m['precision']:.2f}  recall={m['recall']:.2f}  "
              f"f1={m['f1']:.2f}  support={m['support']}")

    print("\n" + "=" * 55)
    print(f"Accuracy:           {report['accuracy']*100:.1f}%")
    print(f"Macro-F1:           {report['macro_f1']*100:.1f}%   <- report THIS, not raw accuracy")
    print(f"Majority baseline:  {report['majority_baseline']*100:.1f}% "
          f"(always guessing '{report['majority_label']}')")
    print(f"Lift over baseline: {(report['accuracy']-report['majority_baseline'])*100:+.1f} points")
    print(f"Total fallback calls: {report['total_fallbacks']}")
    print("=" * 55)


def main():
    if not _backend_is_up():
        print(f"Backend is not reachable at {TRIAGE_URL}. Start it with: py run.py")
        sys.exit(1)

    bugs = json.loads(EVAL_FILE.read_text(encoding="utf-8"))

    # Resume from saved progress if available
    out_path = EVAL_FILE.parent / "predictions.json"
    results = []
    if out_path.exists():
        results = json.loads(out_path.read_text(encoding="utf-8"))
        processed_ids = {r["id"] for r in results}
        print(f"Resuming from {len(results)} already-processed bugs...")
    else:
        processed_ids = set()

    for i, bug in enumerate(bugs):
        bug_id = bug.get("id", "")
        if bug_id in processed_ids:
            continue

        predicted = None
        fallback_calls = 0
        try:
            resp = requests.post(TRIAGE_URL, json=_payload_from_bug(bug), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                predicted = data.get("severity", "").strip().lower()
                agent_outputs = data.get("agent_outputs", [])
                fallback_calls = sum(1 for ao in agent_outputs if ao.get("used_fallback", False))
            else:
                print(f"  Backend {resp.status_code} for {bug_id}: {resp.text[:200]}")
        except requests.RequestException as e:
            print(f"  Exception for {bug_id}: {e}")

        truth = bug.get("ground_truth_severity", "").strip().lower()
        results.append({
            "id": bug_id,
            "truth": truth,
            "predicted": predicted,
            "fallback_calls": fallback_calls,
        })

        # Save incrementally after every bug
        out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

        status = "OK" if predicted == truth else f"MISS (got {predicted}, expected {truth})"
        fwarn = f" [FALLBACK x{fallback_calls}]" if fallback_calls else ""
        print(f"[{len(results)}/{len(bugs)}] {status} - {bug_id}{fwarn}")

        if SLEEP_SECONDS > 0:
            time.sleep(SLEEP_SECONDS)

    print(f"\nSaved raw predictions to {out_path}")
    print_report(compute_report(results))


if __name__ == "__main__":
    main()