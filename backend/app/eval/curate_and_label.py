import json 
import os 

INPUT_FILE = "eval/raw_bugzilla_bugs.json"
OUTPUT_FILE = "eval/bugs.json"
TOP_K = 300


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Bugzilla data already has ground_truth_severity set lol
    # here imma just filter by description length
    filtered = [iss for iss in raw if len(iss.get("description", "")) > 20]
    filtered.sort(key=lambda x: len(x.get("description", "")), reverse=True)

    selected = filtered[:TOP_K]

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(selected, f, indent=2, ensure_ascii=False)

    from collections import Counter
    dist = Counter(b["ground_truth_severity"] for b in selected)
    print(f"Curated {len(selected)} bugs to {OUTPUT_FILE}")
    print("Distribution:")
    for sev, count in sorted(dist.items()):
        print(f"  {sev}: {count}")


if __name__ == "__main__":
    main()