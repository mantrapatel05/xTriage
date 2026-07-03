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

SEVERITY_ORDER = ["low", "medium", "high", "critical"]

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


def get_ground_truth(bug: dict) -> str:
    return str(bug["ground_truth_severity"]).lower()


def max_severity(a: str, b: str) -> str:
    return a if SEVERITY_ORDER.index(a) >= SEVERITY_ORDER.index(b) else b


def call_single_llm(bug: dict, client) -> dict:
    prompt = SINGLE_CALL_PROMPT.format(
        title=bug.get("title", ""), description=bug.get("description", "")
    )
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

    final_severity = max_severity(
        parsed["technical_severity"].lower(), parsed["business_severity"].lower()
    )
    usage = getattr(response, "usage", None)
    tokens = getattr(usage, "total_tokens", 0) or 0

    return {"severity": final_severity, "latency_ms": elapsed_ms, "tokens": tokens}


def call_multi_agent(bug: dict) -> dict:
    payload = {
        "title": bug.get("title", ""),
        "description": bug.get("description", ""),
        "repository": bug.get("repo", ""),
        "issue_url": bug.get("url", ""),
        "labels": bug.get("labels", []),
    }
    t0 = time.perf_counter()
    resp = requests.post(TRIAGE_URL, json=payload, timeout=300)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    resp.raise_for_status()
    data = resp.json()
    return {"severity": data["severity"].lower(), "latency_ms": elapsed_ms}


def main():
    bugs = json.loads(BUGS_PATH.read_text(encoding="utf-8"))
    if BUG_LIMIT > 0:
        bugs = bugs[:BUG_LIMIT]
    n = len(bugs)

    settings = get_settings()
    if not settings.groq_single_api_keys:
        raise RuntimeError("No Groq keys configured for the single-call benchmark.")
    if not settings.groq_multi_api_keys:
        raise RuntimeError("No Groq keys configured for the multi-agent backend.")

    # The FastAPI backend uses get_groq_client(), which defaults to the multi
    # pool. The single-call baseline gets a separate pool from the last two keys.
    single_client = GroqClientPool(
        api_keys=settings.groq_single_api_keys,
        pool_name="single-call",
    )
    reset_token_counter()

    print(
        f"Groq key split: multi-agent={len(settings.groq_multi_api_keys)} key(s), "
        f"single-call={len(settings.groq_single_api_keys)} key(s)"
    )
    if BUG_LIMIT > 0:
        print(f"Benchmark limit active: first {n} bug(s)")

    single_correct = 0
    single_latencies = []
    single_tokens = []

    multi_correct = 0
    multi_latencies = []

    for i, bug in enumerate(bugs, 1):
        truth = get_ground_truth(bug)
        s = {"severity": "ERR", "latency_ms": 0, "tokens": 0}
        m = {"severity": "ERR", "latency_ms": 0}

        try:
            s = call_single_llm(bug, single_client)
            single_correct += s["severity"] == truth
            single_latencies.append(s["latency_ms"])
            single_tokens.append(s["tokens"])
        except Exception as e:
            print(f"[{i}/{n}] single-call ERROR: {e}")

        try:
            m = call_multi_agent(bug)
            multi_correct += m["severity"] == truth
            multi_latencies.append(m["latency_ms"])
        except Exception as e:
            print(f"[{i}/{n}] multi-agent ERROR: {e}")

        print(f"[{i}/{n}] truth={truth:8s}  single={s['severity']:8s}  multi={m['severity']:8s}")
        time.sleep(SLEEP_SECONDS)

    def avg(lst):
        return sum(lst) / len(lst) if lst else 0

    single_total_tokens = get_total_tokens()

    print("\n" + "=" * 60)
    print(f"{'Metric':<28} {'Single-call':>14} {'Multi-agent':>14}")
    print("-" * 60)
    print(f"{'Accuracy':<28} {single_correct/n*100:>13.1f}% {multi_correct/n*100:>13.1f}%")
    print(f"{'Avg latency (ms)':<28} {avg(single_latencies):>14.0f} {avg(multi_latencies):>14.0f}")
    print(f"{'LLM calls per bug':<28} {'1':>14} {'3':>14}")
    print(f"{'Avg tokens per bug':<28} {avg(single_tokens):>14.0f} {'n/a*':>14}")
    print(f"{'Total tokens (all bugs)':<28} {single_total_tokens:>14} {'n/a*':>14}")
    print("=" * 60)
    print("*Multi-agent token cost: run the eval separately via run_eval.py")
    print(" then call get_total_tokens() from a Python shell, or check")
    print(" Groq dashboard for the same time window.")


if __name__ == "__main__":
    main()
