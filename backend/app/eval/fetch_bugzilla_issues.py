"""
fetch_bugzilla_issues.py — pulls a stratified sample of bugs from Mozilla Bugzilla.
Every Bugzilla bug carries a real `severity` field, so no label-guessing needed.

Maps Bugzilla's 6-tier severity to xTriage's 4-tier:
  blocker + critical  -> critical
  major               -> high
  normal              -> medium
  minor + trivial     -> low

Target: ~75 per tier (300 total). Blocker is rare (~6), so critical gets the rest.
"""
import json
import os
import time
import requests

OUTPUT_FILE = "eval/raw_bugzilla_bugs.json"
PER_TIER = 75
SLEEP_BETWEEN_CALLS = 0.5

# Bugzilla severity -> xTriage severity mapping
SEVERITY_MAP = {
    "blocker": "critical",
    "critical": "critical",
    "major": "high",
    "normal": "medium",
    "minor": "low",
    "trivial": "low",
}

# Which Bugzilla severities to pull for each target tier
TIER_QUERIES = {
    "critical": ["blocker", "critical"],
    "high": ["major"],
    "medium": ["normal"],
    "low": ["minor", "trivial"],
}


def fetch_bugs(severity: str, limit: int = 100) -> list[dict]:
    """Fetch bugs from Bugzilla REST API for a given severity."""
    url = "https://bugzilla.mozilla.org/rest/bug"
    params = {
        "severity": severity,
        "resolution": "---",
        "limit": limit,
        "include_fields": "id,severity,summary,description,product,component",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("bugs", [])


def parse_bug(bug: dict, target_severity: str) -> dict:
    """Convert a Bugzilla bug to xTriage schema."""
    return {
        "id": f"bugzilla -- {bug['id']}",
        "source": "bugzilla",
        "repo": f"mozilla/{bug.get('product', 'unknown')}/{bug.get('component', 'unknown')}",
        "url": f"https://bugzilla.mozilla.org/show_bug.cgi?id={bug['id']}",
        "title": bug.get("summary", ""),
        "description": bug.get("description", "") or "",
        "labels": [f"severity:{bug.get('severity', 'unknown')}"],
        "ground_truth_severity": target_severity,
        "ground_truth_team": "manual_label_needed",
    }


def main():
    all_bugs = []
    seen_ids = set()

    for target_tier, bugzilla_severities in TIER_QUERIES.items():
        collected = 0
        for bz_sev in bugzilla_severities:
            if collected >= PER_TIER:
                break
            needed = PER_TIER - collected
            print(f"Fetching {bz_sev} (target tier: {target_tier}, need {needed})...")
            try:
                bugs = fetch_bugs(bz_sev, limit=needed + 20)  # fetch extra for dedup
            except Exception as e:
                print(f"  ERROR fetching {bz_sev}: {e}")
                continue

            for bug in bugs:
                if collected >= PER_TIER:
                    break
                bug_id = bug["id"]
                if bug_id in seen_ids:
                    continue
                seen_ids.add(bug_id)
                all_bugs.append(parse_bug(bug, target_tier))
                collected += 1

            time.sleep(SLEEP_BETWEEN_CALLS)

        print(f"  Collected {collected}/{PER_TIER} for tier '{target_tier}'")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_bugs, f, indent=2, ensure_ascii=False)

    # Print distribution
    from collections import Counter
    dist = Counter(b["ground_truth_severity"] for b in all_bugs)
    print(f"\nDone. Saved {len(all_bugs)} bugs to {OUTPUT_FILE}")
    print("Distribution:")
    for sev, count in sorted(dist.items()):
        print(f"  {sev}: {count}")


if __name__ == "__main__":
    main()