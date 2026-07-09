"""
Quick smoke test — tests 1 bug per severity tier to verify pipeline works end-to-end.
Run from backend/app/eval/ directory while backend is running.
"""
import json
import requests

bugs = json.load(open("backend/app/eval/eval/bugs.json", encoding="utf-8"))

samples = {}
for b in bugs:
    s = b["ground_truth_severity"]
    if s not in samples:
        samples[s] = b

passed = 0
total = 0
total_fallbacks = 0

for sev in sorted(samples.keys()):
    bug = samples[sev]
    # Shorter truncation than full eval (500 vs 2500) for quick smoke test
    payload = {"title": bug["title"][:200], "description": bug["description"][:500]}
    print(f"Testing [{sev}] - {bug['title'][:60]}...")
    try:
        r = requests.post("http://localhost:8000/triage", json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        predicted = data.get("severity", "")
        fallbacks = [ao.get("used_fallback", False) for ao in data.get("agent_outputs", [])]
        any_fallback = any(fallbacks)
        total_fallbacks += sum(fallbacks)
        status = "OK" if predicted == sev else "MISS"
        if status == "OK":
            passed += 1
        total += 1
        print(f"  -> predicted={predicted} fallbacks={fallbacks} [{status}]")
    except Exception as e:
        print(f"  -> ERROR: {e}")

print(f"\n{passed}/{total} passed, {total_fallbacks} total fallback calls")