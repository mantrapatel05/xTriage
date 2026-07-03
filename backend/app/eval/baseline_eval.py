"""
baseline_eval.py — computes dumb baselines to contextualize your model's accuracy.
"""
import json
from collections import Counter
from pathlib import Path

BUGS_PATH = Path("backend/app/eval/eval/bugs.json")
YOUR_MODEL_ACCURACY = 0.82  # <- update after re-running run_eval.py


def get_ground_truth(bug: dict) -> str:
    return str(bug["ground_truth_severity"]).lower()


def main():
    bugs = json.loads(BUGS_PATH.read_text(encoding="utf-8"))
    labels = [get_ground_truth(b) for b in bugs]
    n = len(labels)

    counts = Counter(labels)
    majority_class, majority_count = counts.most_common(1)[0]
    majority_baseline = majority_count / n

    distinct_levels = len(counts)
    uniform_random_baseline = 1 / distinct_levels

    # weighted random = guess each class proportional to its real frequency
    weighted_random_baseline = sum((c / n) ** 2 for c in counts.values())

    print("=" * 55)
    print(f"Total labelled bugs: {n}")
    print("Class distribution:")
    for level, c in counts.most_common():
        print(f"  {level:10s} {c:4d}  ({c/n*100:.1f}%)")
    print("-" * 55)
    print(f"Majority-class baseline  (always guess '{majority_class}'): {majority_baseline*100:.1f}%")
    print(f"Uniform random baseline  ({distinct_levels} classes)        : {uniform_random_baseline*100:.1f}%")
    print(f"Weighted random baseline (matches class distribution)     : {weighted_random_baseline*100:.1f}%")
    print("=" * 55)
    lift = (YOUR_MODEL_ACCURACY - majority_baseline) * 100
    print(f"\nxTriage model: {YOUR_MODEL_ACCURACY*100:.1f}%")
    print(f"Lift over majority-class baseline: {lift:+.1f} points")


if __name__ == "__main__":
    main()