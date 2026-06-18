# converting here the text to vector embeddings following vector store and duplicate detector
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

class EmbeddingsService:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)

    def embed_text(self, text: str) -> list[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()
    
    def embed_batch(self, texts : list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return [emb.tolist() for emb in embeddings]
    
    def embed_bug(self, title:str, description:str) -> list[float]:
        combine = f"{title}\n{description}"
        return self.embed_text(combine)