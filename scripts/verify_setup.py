import os
from dotenv import load_dotenv
import redis
import psycopg2
from qdrant_client import QdrantClient

load_dotenv()

# Check Redis
r = redis.from_url(os.getenv("REDIS_URL"))
r.ping()
print("Redis connected")

# Check PostgreSQL
conn = psycopg2.connect(os.getenv("POSTGRES_URL"))
conn.close()
print("PostgreSQL connected")

# Check Qdrant
client = QdrantClient(url=os.getenv("QDRANT_URL"))
client.get_collections()
print("Qdrant connected")

print("\n All systems ready!")