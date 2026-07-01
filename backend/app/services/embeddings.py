import os
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingsService:
    def __init__(self):
        allow_download = os.getenv("XTRIAGE_EMBEDDINGS_ALLOW_DOWNLOAD", "").lower() in {"1", "true", "yes"}
        self.model = SentenceTransformer(MODEL_NAME, local_files_only=not allow_download)

    def embed_text(self, text: str) -> list[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return [embedding.tolist() for embedding in embeddings]

    def embed_bug(self, title: str, description: str) -> list[float]:
        combined = f"{title}\n{description}"
        return self.embed_text(combined)
