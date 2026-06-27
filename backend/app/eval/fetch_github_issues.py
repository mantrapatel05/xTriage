import requests
import json
import os 

# https://github.com/microsoft/vscode/issues
# parent(folder) == microsoft and child(its project) == vscode
OWNER = "microsoft"
REPO = "vscode"
BUG_LABEL = "bug"
OUTPUT_FILE = "eval/raw_github_bugs.json"
# GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# fetch = "https://github.com/microsoft/vscode/issues"
headers = {"accept" : "application/vnd.github.v3+json"}

# print(response.status_code)
# to fetch the one page of issues
def fetch_page(page=1,per_page=100):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"
    params = {
        "state" : "all",
        "labels" : BUG_LABEL,
        "page" : page,
        "per_page" : per_page,
        "sort" : "created",
        "direction" : "desc"
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# getting the github api issue acc to our needs
def parse_issue(issue):
    if "pull_request" in issue:
        return

    return{
        "id" : f"{OWNER} -- {REPO} -- {issue['number']}",
        "source" : "github",
        "repo" : f"{OWNER}/{REPO}",
        "url" : issue["html_url"],
        "title" : issue["title"],
        "description": issue["body"] or "",
        "labels" : [lbl["name"] for lbl in issue["labels"]],
        "ground_truth_severity" : "manual_label_needed",
        "ground_truth_team" : "manual_label_needed"
    } 

def main():
    all_issues = []
    max_pages = 3
    per_page = 100

    for page in range(1 , max_pages + 1):
        print(f"fetching page...")
        try:
            raw_page =  fetch_page(page,per_page)
        except requests.exceptions.HTTPError as e:
            print("rate limit hit")
            print(f"stopped at page {page} : {e}")
            break

        if not raw_page:
            break
        for issue in raw_page:
            parsed = parse_issue(issue)
            if parsed:
                all_issues.append(parsed)

    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_issues, f, indent=2, ensure_ascii=False)

    print(f"done. saved {len(all_issues)} issues to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()