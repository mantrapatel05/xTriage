"""
agent_benchmark.py — compares your 3-agent pipeline against a single
consolidated LLM call, on the same 100 labelled bugs. Measures accuracy,
latency, and token usage (cost proxy) for both.
"""
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
import requests

load_dotenv()

# Add project root so we can import the shared Groq client pool
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from backend.app.config import get_settings
from backend.app.services.groq_client import GroqClientPool, reset_token_counter, get_total_tokens

BUGS_PATH = Path(__file__).resolve().parent / "eval" / "bugs.json"
TRIAGE_URL = os.environ.get("TRIAGE_URL", "http://localhost:8000/triage")
GROQ_MODEL = "llama-3.1-8b-instant"
SLEEP_SECONDS = float(os.environ.get("EVAL_SLEEP_SECONDS", "5"))
BUG_LIMIT = int(os.environ.get("EVAL_BUG_LIMIT", "0"))
SINGLE_RESULTS_PATH = Path(__file__).resolve().parent / "eval" / "agent_benchmark_single.json"
MULTI_RESULTS_PATH = Path(__file__).resolve().parent / "eval" / "agent_benchmark_multi.json"

SEVERITY_ORDER = ["low", "medium", "high", "critical"]
BUGZILLA_SEVERITY_MAP = {
    "blocker": "critical",
    "critical": "critical",
    "major": "high",
    "normal": "medium",
    "minor": "low",
    "trivial": "low",
}

SINGLE_CALL_PROMPT = """You are a bug triage assistant. Given the bug report below, \
return ONLY valid JSON (no markdown, no prose) with this exact shape:

{{
  "technical_severity": "low" | "medium" | "high" | "critical",
  "business_severity": "low" | "medium" | "high" | "critical",
  "assigned_team": "<team name>",
  "confidence": <float 0.0-1.0>
}}

Bug title: {title}
Bug description: {description}
"""


def _truncate(value: str | None, max_chars: int) -> str:
    if not value:
        return ""
    return str(value)[:max_chars]


def _write_json(path: Path, data: list[dict]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _payload_from_bug(bug: dict) -> dict:
    return {
        "bug_id": bug.get("id"),
        "title": _truncate(bug.get("title"), 200),
        "description": _truncate(bug.get("description"), 2500),
        "repository": bug.get("repo"),
        "issue_url": bug.get("url"),
        "labels": bug.get("labels", []),
    }


def _normalize_severity(value: str, *, bug_label: str, field_name: str) -> str:
    raw_value = str(value).strip().lower()
    normalized = BUGZILLA_SEVERITY_MAP.get(raw_value, raw_value)
    if normalized != raw_value:
        print(
            f"[warn] normalized {field_name} severity for {bug_label}: "
            f"{raw_value!r} -> {normalized!r}"
        )
    if normalized not in SEVERITY_ORDER:
        print(
            f"[warn] unrecognized {field_name} severity for {bug_label}: "
            f"{raw_value!r}; defaulting to 'low'"
        )
        return "low"
    return normalized


def _log_422_response(resp: requests.Response, bug_label: str) -> None:
    try:
        body = resp.json()
    except ValueError:
        body = resp.text
    print(f"[{bug_label}] triage 422 response body: {body}")


def get_ground_truth(bug: dict) -> str:
    return str(bug["ground_truth_severity"]).lower()


def max_severity(a: str, b: str) -> str:
    return a if SEVERITY_ORDER.index(a) >= SEVERITY_ORDER.index(b) else b


def call_single_llm(bug: dict, client) -> dict:
    prompt = SINGLE_CALL_PROMPT.format(
        title=_truncate(bug.get("title"), 200),
        description=_truncate(bug.get("description"), 2500),
    )
    bug_label = str(bug.get("id") or bug.get("title") or "<unknown>")
    t0 = time.perf_counter()
    response = client.chat_completions_create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=220,
        temperature=0,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000

    raw = response.choices[0].message.content.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    parsed = json.loads(raw)

    technical_severity = _normalize_severity(
        parsed["technical_severity"], bug_label=bug_label, field_name="technical"
    )
    business_severity = _normalize_severity(
        parsed["business_severity"], bug_label=bug_label, field_name="business"
    )
    final_severity = max_severity(
        technical_severity, business_severity
    )
    usage = getattr(response, "usage", None)
    tokens = getattr(usage, "total_tokens", 0) or 0

    return {"severity": final_severity, "latency_ms": elapsed_ms, "tokens": tokens}


def call_multi_agent(bug: dict) -> dict:
    payload = _payload_from_bug(bug)
    bug_label = str(bug.get("id") or bug.get("title") or "<unknown>")
    t0 = time.perf_counter()
    resp = requests.post(TRIAGE_URL, json=payload, timeout=300)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    if resp.status_code == 422:
        _log_422_response(resp, bug_label)

    resp.raise_for_status()
    data = resp.json()
    return {"severity": data["severity"].lower(), "latency_ms": elapsed_ms}


def run_single_call_phase(bugs: list[dict], client) -> tuple[int, list[float], list[int]]:
    results: list[dict] = []
    correct = 0
    latencies: list[float] = []
    tokens: list[int] = []

    for i, bug in enumerate(bugs, 1):
        truth = get_ground_truth(bug)
        result = {"severity": "ERR", "latency_ms": 0, "tokens": 0}

        try:
            result = call_single_llm(bug, client)
            correct += result["severity"] == truth
            latencies.append(result["latency_ms"])
            tokens.append(result["tokens"])
        except Exception as e:
            print(f"[{i}/{len(bugs)}] single-call ERROR: {e}")

        results.append(
            {
                "id": bug.get("id", ""),
                "truth": truth,
                "predicted": result["severity"],
                "latency_ms": result["latency_ms"],
                "tokens": result["tokens"],
            }
        )
        _write_json(SINGLE_RESULTS_PATH, results)
        print(f"[{i}/{len(bugs)}] truth={truth:8s}  single={result['severity']:8s}")
        time.sleep(SLEEP_SECONDS)

    return correct, latencies, tokens


def run_multi_agent_phase(bugs: list[dict]) -> tuple[int, list[float]]:
    results: list[dict] = []
    correct = 0
    latencies: list[float] = []

    for i, bug in enumerate(bugs, 1):
        truth = get_ground_truth(bug)
        result = {"severity": "ERR", "latency_ms": 0}

        try:
            result = call_multi_agent(bug)
            correct += result["severity"] == truth
            latencies.append(result["latency_ms"])
        except Exception as e:
            print(f"[{i}/{len(bugs)}] multi-agent ERROR: {e}")

        results.append(
            {
                "id": bug.get("id", ""),
                "truth": truth,
                "predicted": result["severity"],
                "latency_ms": result["latency_ms"],
            }
        )
        _write_json(MULTI_RESULTS_PATH, results)
        print(f"[{i}/{len(bugs)}] truth={truth:8s}  multi={result['severity']:8s}")
        time.sleep(SLEEP_SECONDS)

    return correct, latencies


def main():
    bugs = json.loads(BUGS_PATH.read_text(encoding="utf-8"))
    if BUG_LIMIT > 0:
        bugs = bugs[:BUG_LIMIT]
    n = len(bugs)

    settings = get_settings()
    benchmark_keys = tuple(
        dict.fromkeys(
            list(settings.groq_api_keys)
            + list(settings.groq_multi_api_keys)
            + list(settings.groq_single_api_keys)
        )
    )
    if not benchmark_keys:
        raise RuntimeError("No Groq keys configured for the single-call benchmark.")
    if not settings.groq_multi_api_keys:
        raise RuntimeError("No Groq keys configured for the multi-agent backend.")

    # Run the single-call benchmark first with the full Groq key set, then the
    # multi-agent backend second so neither phase competes for the same quota.
    single_client = GroqClientPool(
        api_keys=benchmark_keys,
        pool_name="single-call",
    )
    reset_token_counter()

    print(f"Groq keys available: {len(benchmark_keys)} total")
    if BUG_LIMIT > 0:
        print(f"Benchmark limit active: first {n} bug(s)")

    single_correct, single_latencies, single_tokens = run_single_call_phase(bugs, single_client)
    single_total_tokens = get_total_tokens()

    multi_correct, multi_latencies = run_multi_agent_phase(bugs)

    def avg(lst):
        return sum(lst) / len(lst) if lst else 0

    print("\n" + "=" * 60)
    print(f"{'Metric':<28} {'Single-call':>14} {'Multi-agent':>14}")
    print("-" * 60)
    print(f"{'Accuracy':<28} {single_correct/n*100:>13.1f}% {multi_correct/n*100:>13.1f}%")
    print(f"{'Avg latency (ms)':<28} {avg(single_latencies):>14.0f} {avg(multi_latencies):>14.0f}")
    print(f"{'LLM calls per bug':<28} {'1':>14} {'3':>14}")
    print(f"{'Avg tokens per bug':<28} {avg(single_tokens):>14.0f} {'n/a*':>14}")
    print(f"{'Total tokens (all bugs)':<28} {single_total_tokens:>14} {'n/a*':>14}")
    print("=" * 60)
    print(f"Single-call results saved to {SINGLE_RESULTS_PATH}")
    print(f"Multi-agent results saved to {MULTI_RESULTS_PATH}")
    print("*Multi-agent token cost: run the eval separately via run_eval.py")
    print(" then call get_total_tokens() from a Python shell, or check")
    print(" Groq dashboard for the same time window.")


if __name__ == "__main__":
    main()
