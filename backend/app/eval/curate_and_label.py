import json 
import os 

INPUT_FILE = "eval/raw_github_bugs.json"
OUTPUT_FILE = "eval/bugs.json"
# final length of bugs how many to keep
# 50 or 100
TOP_K = 100
MIN_DISC_LENGTH = 80

# mapping based of the github issue that i fetched
LABEL_TO_SEVERITY  = {
    "critical" : "critical",
    "severity : critical" : " critical",
    "p0" : "critical",
    "high" : "high",
    "severity : high" : "high",
    "severe" : "high",
    "important" : "high",
    "p1" : "high",
    "medium" : "medium",
    "severity : medium" : "medium",
    "p2" : "medium",
    "low" : "low",
    "severity : low" : "low",
    "minor" : "low",
    "p3" : "low",
    "p4" : "low" 
}

def map_severity(labels):
    for label in labels:
        key = label.lower()
        if key in LABEL_TO_SEVERITY:
            return LABEL_TO_SEVERITY[key]
    return None

def quality_score(issue):
    score = 0
    desc = issue.get("description","")
    if len(desc) > 200:
        score += 3
    elif len(desc) > 100:
        score += 2
    elif len(desc) > 50:
        score += 1

    score += min(len(issue.get("labels",[])),5)
    return score

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    filtered = [iss for iss in raw if len(iss.get("description"))]
    
    # trying to auto assign severity from labels 
    labeled = []
    unlabeled = []
    for iss in filtered:
        sev = map_severity(iss["labels"])
        if sev:
            iss["ground_truth_severity"] = sev
            labeled.append(iss)
        else:
            unlabeled.append(iss)

    labeled.sort(key=quality_score,reverse=True)
    unlabeled.sort(key=quality_score,reverse=True)

    selected = (labeled + unlabeled)[:TOP_K]

    # default rem issues to medium labelling
    for iss in selected:
        if iss['ground_truth_severity'] == "manual_label_needed":
            iss["ground_truth_severity"] = "medium"

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(selected,f,indent=2,ensure_ascii=False)

    print(f"curated {len(selected)} curated bugs to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
