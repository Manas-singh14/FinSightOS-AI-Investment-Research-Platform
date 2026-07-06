from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os

# load the embedding model
# this converts text into vectors that capture meaning
# all-MiniLM-L6-v2 is small, fast, free, runs on CPU
model = SentenceTransformer('all-MiniLM-L6-v2')

# connect to qdrant running in docker
client = QdrantClient(url="http://localhost:6333")

def chunk_by_topic(filepath: str) -> list:
    # our file already separates concepts by "TOPIC:" markers
    # split on that instead of arbitrary word counts
    # this keeps each concept complete and coherent
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    chunks = content.split("TOPIC:")
    chunks = [c.strip() for c in chunks if c.strip()]
    return chunks


def build_index():
    chunks = chunk_by_topic("data/docs/financial_concepts.txt")
    print(f"Found {len(chunks)} concept chunks")

    # create collection in qdrant
    # vector size 384 matches all-MiniLM-L6-v2 output dimension
    client.recreate_collection(
        collection_name="financial_concepts",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

    points = []
    for i, chunk in enumerate(chunks):
        # convert text to embedding vector
        vector = model.encode(chunk).tolist()

        points.append(
            PointStruct(
                id=i,
                vector=vector,
                payload={"text": chunk}
            )
        )

    # upload all chunks at once
    client.upsert(
        collection_name="financial_concepts",
        points=points
    )

    print(f"Indexed {len(points)} chunks into Qdrant")


if __name__ == "__main__":
    build_index()