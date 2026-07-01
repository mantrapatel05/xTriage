import json
import os
import sys
import time
from pathlib import Path

import requests


EVAL_FILE = Path(__file__).resolve().parent / "eval" / "bugs.json"
TRIAGE_URL = os.getenv("TRIAGE_URL", "http://localhost:8000/triage")
REQUEST_TIMEOUT = int(os.getenv("EVAL_REQUEST_TIMEOUT", "300"))
SLEEP_SECONDS = float(os.getenv("EVAL_SLEEP_SECONDS", "5"))


def _payload_from_bug(bug: dict) -> dict:
    return {
        "bug_id": bug.get("id"),
        "title": bug["title"],
        "description": bug["description"],
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


def main():
    if not _backend_is_up():
        print(f"Backend is not reachable at {TRIAGE_URL}. Start it with: py run.py")
        sys.exit(1)

    with EVAL_FILE.open("r", encoding="utf-8") as f:
        bugs = json.load(f)

    correct = 0
    total = 0
    errors = 0

    for i, bug in enumerate(bugs):
        payload = _payload_from_bug(bug)
        predicted = None

        try:
            resp = requests.post(TRIAGE_URL, json=payload, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                result = resp.json()
                predicted = result.get("severity", "").strip().lower()
            else:
                print(f"  Backend {resp.status_code} for {bug['id']}: {resp.text[:300]}")
                errors += 1
        except requests.RequestException as e:
            print(f"  Exception for {bug['id']}: {e}")
            errors += 1

        ground = bug.get("ground_truth_severity", "").strip().lower()
        total += 1

        if predicted and predicted == ground:
            correct += 1
            status = "OK"
        elif predicted:
            status = f"MISS (got {predicted}, expected {ground})"
        else:
            status = "ERROR"

        print(f"[{i + 1}/{len(bugs)}] {status} - {bug['id']} - {bug['title'][:70]}")

        if SLEEP_SECONDS > 0:
            time.sleep(SLEEP_SECONDS)

    accuracy = (correct / total) * 100 if total > 0 else 0
    print("\n" + "=" * 50)
    print(f"Severity Accuracy: {correct}/{total} = {accuracy:.1f}%")
    print(f"Errors: {errors}")
    print("=" * 50)


if __name__ == "__main__":
    main()
