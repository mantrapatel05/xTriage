import requests
import json
import os

# Fetch from multiple repos that actually use severity labels like "bug:high", "priority/critical", etc.
REPOS = [
    ("microsoft", "vscode"),
    ("django", "django"),
    ("ansible", "ansible"),
    ("home-assistant", "core"),
    ("godotengine", "godot"),
]
BUG_LABEL = "bug"
OUTPUT_FILE = "eval/raw_github_bugs.json"
MAX_PAGES = 3
PER_PAGE = 100

headers = {"accept": "application/vnd.github.v3+json"}


def fetch_page(owner, repo, page=1, per_page=100):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    params = {
        "state": "all",
        "labels": BUG_LABEL,
        "page": page,
        "per_page": per_page,
        "sort": "created",
        "direction": "desc",
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def parse_issue(issue, owner, repo):
    if "pull_request" in issue:
        return None
    return {
        "id": f"{owner} -- {repo} -- {issue['number']}",
        "source": "github",
        "repo": f"{owner}/{repo}",
        "url": issue["html_url"],
        "title": issue["title"],
        "description": issue["body"] or "",
        "labels": [lbl["name"] for lbl in issue["labels"]],
        "ground_truth_severity": "manual_label_needed",
        "ground_truth_team": "manual_label_needed",
    }


def main():
    all_issues = []

    for owner, repo in REPOS:
        print(f"Fetching {owner}/{repo}...")
        for page in range(1, MAX_PAGES + 1):
            print(f"  page {page}...")
            try:
                raw_page = fetch_page(owner, repo, page, PER_PAGE)
            except requests.exceptions.HTTPError as e:
                print(f"  stopped at page {page}: {e}")
                break

            if not raw_page:
                break

            for issue in raw_page:
                parsed = parse_issue(issue, owner, repo)
                if parsed:
                    all_issues.append(parsed)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_issues, f, indent=2, ensure_ascii=False)

    print(f"Done. Saved {len(all_issues)} issues to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()