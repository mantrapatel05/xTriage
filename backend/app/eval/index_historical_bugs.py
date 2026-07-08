from __future__ import annotations
import json 
from pathlib import Path
from typing import Any

from backend.app.services.vector_store import VectorStore

HISTORICAL_BUGS_PATH = Path(__file__).resolve().parent / "eval" / "bugs.json"

def load_historical_bugs() -> list[dict[str, Any]]:
    with HISTORICAL_BUGS_PATH.open("r",encoding="utf-8") as f:
        raw_bugs=json.load(f)

        if not isinstance(raw_bugs,list):
            raise ValueError("bugs.json must be a JSON array!!!")
        
        bugs: list[dict[str,Any]] = []
        for item in raw_bugs:
            if not isinstance(item, dict):
                continue
            bug_id = str(item.get("bug_id") or item.get("id") or "")
            title = str(item.get("title") or "")
            description = str(item.get("description") or "")
            severity = str(item.get("ground_truth_severity") or item.get("severity") or "unknown")
            resolution = str(item.get("resolution") or item.get("ground_truth_resolution") or "unknown")
            component = str(item.get("component") or item.get("repo") or "unknown")
            team = str(item.get("ground_truth_team") or item.get("team") or "unknown")

            bugs.append({
                "bug_id" : bug_id,
                "id" : bug_id,
                "title" : title,
                "description" : description,
                "severity" : severity,
                "resolution" : resolution,
                "component" : component,
                "team" : team,
                "issue_url" : str(item.get("url") or item.get("issue_url") or ""),
                "source" : str(item.get("source") or "unknown"),
                "repo": str(item.get("repo") or "unknown"),
                "labels": item.get("labels", []),
            })
        return bugs
    
def seed_load_vector_store() -> int:
    bugs = load_historical_bugs()
    store = VectorStore()
    store.clear_collection()
    if bugs:
        store.add_bugs_batch(bugs)
    return len(bugs)

if __name__ == "__main__":
    seeded = seed_load_vector_store()
    print(f"Seeded {seeded} historical bugs into vector store")