from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# load once, reuse across calls
# loading model every time would be slow
model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient(url="http://localhost:6333")


# def search_financial_concepts(query: str, top_k: int = 2) -> list:
#     # converts user question to vector, finds closest matching
#     # concept explanations from our knowledge base
#     query_vector = model.encode(query).tolist()

#     results = client.query_points(
#         collection_name="financial_concepts",
#         query=query_vector,
#         limit=top_k
#     )

#     return [
#         {
#             "text": r.payload['text'],
#             "relevance_score": round(r.score, 3)
#         }
#         for r in results.points
#     ]

def search_financial_concepts(query: str, top_k: int = 2) -> list:
    try:
        query_vector = model.encode(query).tolist()
        results = client.query_points(
            collection_name="financial_concepts",
            query=query_vector,
            limit=top_k
        )
        return [
            {
                "text": r.payload['text'],
                "relevance_score": round(r.score, 3)
            }
            for r in results.points
        ]
    except Exception:
        # if qdrant is down, return empty list
        # agents will work without RAG context
        return []

if __name__ == "__main__":
    # quick test
    results = search_financial_concepts("explain beta and stock volatility")
    for r in results:
        print(f"Score: {r['relevance_score']}")
        print(f"Text: {r['text'][:150]}")
        print()