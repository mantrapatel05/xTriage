import uuid
from datetime import datetime,timezone

import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.app.services.embeddings import EmbeddingsService

COLLECTION_NAME = "bug-embeddings"

class VectorStore:
    def __init__(self):
        self.client = chromadb.Client(
            ChromaSettings(
                persist_directory = "./chroma_data",
                anonymized_telemetry=False,
            )
        )
        self.embedder = EmbeddingsService()
        self.collection = self.get_or_create_collection()
    
    def get_or_create_collection(self):
        try:
            return self.client.get_collection(COLLECTION_NAME)
        except:
            return self.client.create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space":"cosine"},
            )
        
    def add_bug(self, bug_id : str, title : str, description : str, metadata : dict | None = None) -> None:
        # storing the bug and its embedding in chromadb
        embedding = self.embedder.embed_bug(title,description)
        meta = metadata or {}
        meta.update({"title":title,"description":description})
        self.collection.add(
            ids=[bug_id or str(uuid.uuid4())],
            embeddings=[embedding],
            metadatas=[meta],
        )
    
    def add_bugs_batch(self, bugs : list[dict]) -> None:  # BUG FIXED: renamed from find_similar (duplicate name) to add_bugs_batch, it was overwriting the real find_similar method
        ids,embeddings,metadatas = [],[],[]
        for bug in bugs:
            bug_id = bug.get("bug_id") or str(uuid.uuid4())
            title = bug.get("title","")
            description = bug.get("description","")
            embedding = self.embedder.embed_bug(title,description)
            meta = {k:v for k,v in bug.items() if k not in ("bug_id",)}
            meta["description"] = description[:500]  # BUG FIXED: was "deescription" (typo)
            ids.append(bug_id)
            embeddings.append(embedding)
            metadatas.append(meta)
        self.collection.add(ids=ids,embeddings=embeddings, metadatas=metadatas)

    # finding the topk most similar bugs
    def find_similar(self, title: str, description: str, top_k: int = 5, threshold: float = 0.5) -> list[dict]:
        query_embedding = self.embedder.embed_bug(title,description)
        results= self.collection.query(
			query_embeddings=[query_embedding],  # BUG FIXED: was `query_embedding` (singular) but chromadb expects `query_embeddings` (plural)
			n_results=top_k,
			include=["metadatas","distances"],
		)
        matches = []
        if results["ids"][0]:
            for i, bug_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]  # BUG FIXED: was `results["distance"]` but chromadb returns `distances` (plural)
                similarity = round(1 - distance, 4)
                if similarity >= threshold:
                    meta = results["metadatas"][0][i]  # BUG FIXED: was `results["metadata"]` but chromadb returns `metadatas` (plural)
                    matches.append({
                        "bug_id" : bug_id,
                        "title" : meta.get("title","Unknown"),
                        "similarity" : similarity,
                        "description":meta.get("description",""),
                        "issue_url" : meta.get("issue_url",""),
                    })
        return matches  # BUG FIXED: was not returning anything if the if condition was false (fell off the function returning None)