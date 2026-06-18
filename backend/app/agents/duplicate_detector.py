from backend.app.models.bug import BugReport
from backend.app.models.triage_result import AgentOutput, DuplicateMatch
from backend.app.services.vector_store import VectorStore

DUPLICATE_THRESHOLD = 0.75
SIMILAR_THRESHOLD = 0.45

class DuplicateDetector:
    def __init__(self):
        self.store = VectorStore()
    
    def search(self, bug : BugReport) -> tuple[list[DuplicateMatch], AgentOutput]:
        matches = self.store.find_similar(
            title=bug.title,
            description=bug.description,
            top_k=5,
            threshold=SIMILAR_THRESHOLD,
        )

        duplicate_matches = []
        for m in matches:
            duplicate_matches.append(
                DuplicateMatch(
                    bug_id=m.get("bug_id"),
                    title=m.get("title","Unknown"),
                    similarity=m["similarity"],  # BUG FIXED: was ["similarity"] (list literal) instead of m["similarity"]
                    rationale=f"Similarity score : {m['similarity']:.0%}",
                    issue_url=m.get("issue_url"),
                )
            )

        top_similarity = matches[0]["similarity"] if matches else 0.0
        if top_similarity >= DUPLICATE_THRESHOLD:
            decision = "duplicate_found"  # BUG FIXED: removed trailing comma (was creating a tuple) and fixed typo "duplcate_found" -> "duplicate_found"
            rationale = f"Duplicate detected : {matches[0]['title']} ({top_similarity:.0%} similar)"
            confidence = round(min(top_similarity + 0.05, 1.0), 2)
        elif top_similarity >= SIMILAR_THRESHOLD:
            decision = "similar_found"
            rationale = f"No exact duplicate, but {len(matches)} related bugs found"
            confidence = round(top_similarity,2)
        else:
            decision = "no_duplicate"
            rationale = "No similar bugs found in the database"
            confidence=0.9

        agent_output = AgentOutput(
            agent_name="duplicate_detector",
            decision=decision,
            rationale=rationale,
            confidence=confidence,
            signals=[m.title for m in duplicate_matches],
        )

        return duplicate_matches,agent_output