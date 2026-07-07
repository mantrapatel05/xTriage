import chromadb
import uuid
from embeddings import EmbeddingsService

COLLECTION_NAME = "bug-embeddings"

class VectorStore:
    def __init__(self,embedder=None, client=None) -> None:
        self.embedder = embedder if embedder is not None else EmbeddingsService()
        self.client = client or chromadb.PersistentClient(path="./chroma_data")
        self.collection = self.get_or_create_collection()

    def get_or_create_collection(self) -> any:
        try:
            return self.client.get_collection(COLLECTION_NAME)
        except Exception:
            return self.client.create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space":"cosine"}
            )
        
    def clear_collection(self) -> None:
        try:
            self.client.delete_collection(name=COLLECTION_NAME)
        except Exception:
            pass
        self.collection = self.client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    
    def count(self)->int:
        return self.collection.count()
    
    def is_empty(self) -> bool:
        return self.count() == 0

    # here we worked on ingesting the data
    def add_bug(self, bug_id : str, title : str, description : str, metadata : dict | None = None) -> None:
        document = f"Title: {title}\nDescription: {description}"
        embedding = self.embedder.embed_bug(title, description)
        meta = metadata.copy() if metadata else {}
        meta.update({"title":title,"description":description[:500],"bug_id":bug_id})

        self.collection.add(
            ids=[bug_id],
            documents=[document],
            embeddings=[embedding],
            metadatas=[meta]
        )
    
    def normalize_metadata(self, bug:dict, bug_id:str, title:str, description:str) -> dict[str, str]:
        severity = str(bug.get("severity") or bug.get("ground_truth_severity") or bug.get("severity_hint") or "unknown")
        resolution = str(bug.get("resolution") or bug.get("ground_truth_resolution") or "unknown")
        component = str(bug.get("component") or bug.get("repo") or "unknown")
        team = str(bug.get("team") or bug.get("ground_truth_team") or "unknown")

        return {
            "bug_id":bug_id,
            "title":title,
            "description":description,
            "severity":severity,
            "resolution":resolution,
            "component":component,
            "team":team,
            "issue_url":str(bug.get("issue_url") or bug.get("url") or ""),
            "source" : str(bug.get("source") or "unknown")
        }

    def add_bugs_batch(self, bugs : list[dict]) -> None:
        if not bugs:
            return 
        
        ids, documents, embeddings, metadatas = [],[],[],[]
        for bug in bugs:    
            bug_id = bug.get("bug_id") or bug.get("id") or str(uuid.uuid4())
            title = bug.get("title","")
            description = bug.get("description","")
            document = f"Title : {title}\nDescription: {description}"   
            embedding = self.embedder.embed_bug(title, description) 
            metadata = self.normalize_metadata(bug, bug_id, title, description)

            ids.append(bug_id)
            documents.append(document)
            embeddings.append(embedding)
            metadatas.append(metadata)

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
    
    # here we worked on retriving the data ingested already
    def find_similar_bug(self, title : str="", description : str="", query:str | None=None, top_k : int = 5, threshold : float=0.5)-> list[dict]:
        
        q = query if query else f"{title}\n{description}"
        query_embedding = self.embedder.embed_text(q)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents","distances","metadatas"]
        )

        # here chromadb will return everything inside single-element list
        # we are sending one query vectorr
        ids = results["ids"][0]
        documents = results["documents"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]

        matches = []
        for i,bug_id in enumerate(ids):
            similarity = round(1 - float(distances[i]), 4)
            metadata = metadatas[i] or {}
            if similarity < threshold:
                continue
            matches.append({
                "bug_id":bug_id,
                "document":documents[i],
                "similarity": similarity,
                "title" : metadata.get("title",documents[i].split("\n")[0].replace("Title: ","")),
                "metadata" :metadata 
            })
        return matches

    def retrieve_similar_with_metadata(self, query:str, n_results: int=3, threshold:float=0.5) -> list[dict]:
        return self.find_similar_bug(query=query, top_k=n_results, threshold=threshold)