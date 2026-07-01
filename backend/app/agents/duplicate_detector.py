from backend.app.models.bug import BugReport
from backend.app.models.triage_result import AgentOutput, DuplicateMatch
from backend.app.services.vector_store import VectorStore


DUPLICATE_THRESHOLD = 0.75
SIMILAR_THRESHOLD = 0.45


class DuplicateDetector:
    def __init__(self):
        try:
            self.store = VectorStore()
            self.available = True
        except Exception as e:
            print(f"  [DuplicateDetector] Duplicate search unavailable: {e}")
            self.store = None
            self.available = False

    def search(self, bug: BugReport) -> tuple[list[DuplicateMatch], AgentOutput]:
        if not self.available or self.store is None:
            return self._unavailable_output("Duplicate search unavailable; continuing triage without similarity matches")

        try:
            matches = self.store.find_similar(
                title=bug.title,
                description=bug.description,
                top_k=5,
                threshold=SIMILAR_THRESHOLD,
            )
        except Exception as e:
            print(f"  [DuplicateDetector] Duplicate search failed: {e}")
            return self._unavailable_output("Duplicate search failed; continuing triage without similarity matches")

        duplicate_matches = [
            DuplicateMatch(
                bug_id=match.get("bug_id"),
                title=match.get("title", "Unknown"),
                similarity=match["similarity"],
                rationale=f"Similarity score: {match['similarity']:.0%}",
                issue_url=match.get("issue_url"),
            )
            for match in matches
        ]

        top_similarity = matches[0]["similarity"] if matches else 0.0

        if top_similarity >= DUPLICATE_THRESHOLD:
            decision = "duplicate_found"
            rationale = f"Duplicate detected: {matches[0]['title']} ({top_similarity:.0%} similar)"
            confidence = round(min(top_similarity + 0.05, 1.0), 2)
        elif top_similarity >= SIMILAR_THRESHOLD:
            decision = "similar_found"
            rationale = f"No exact duplicate, but {len(matches)} related bugs found"
            confidence = round(top_similarity, 2)
        else:
            decision = "no_duplicate"
            rationale = "No similar bugs found in the database"
            confidence = 0.9

        return duplicate_matches, AgentOutput(
            agent_name="duplicate_detector",
            decision=decision,
            rationale=rationale,
            confidence=confidence,
            signals=[match.title for match in duplicate_matches],
        )

    def _unavailable_output(self, rationale: str) -> tuple[list[DuplicateMatch], AgentOutput]:
        return [], AgentOutput(
            agent_name="duplicate_detector",
            decision="duplicate_check_unavailable",
            rationale=rationale,
            confidence=0.0,
            signals=[],
        )
