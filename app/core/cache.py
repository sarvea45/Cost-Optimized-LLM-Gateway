import json
import numpy as np
from redis.asyncio import Redis
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.exceptions import ResponseError
from litellm import acompletion
from app.config import settings, yaml_config

redis_client = Redis.from_url(settings.redis_url, decode_responses=False)
INDEX_NAME = "prompt_idx"

async def init_redis_index():
    try:
        await redis_client.ft(INDEX_NAME).info()
    except ResponseError:
        # Index doesn't exist, create it
        schema = (
            TextField("response"),
            VectorField(
                "embedding",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": 1536, # text-embedding-3-small dimension
                    "DISTANCE_METRIC": "COSINE"
                }
            )
        )
        definition = IndexDefinition(prefix=["prompt:"], index_type=IndexType.HASH)
        await redis_client.ft(INDEX_NAME).create_index(fields=schema, definition=definition)

async def get_embedding(text: str) -> list[float]:
    model = yaml_config.get("models", {}).get("embedding", "text-embedding-3-small")
    response = await acompletion(model=model, input=text)
    return response.data[0]["embedding"]

async def check_cache(embedding: list[float], threshold: float) -> str | None:
    embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
    query = (
        f"*=>[KNN 1 @embedding $vec AS score]"
    )
    from redis.commands.search.query import Query
    q = Query(query).sort_by("score").return_fields("response", "score").dialect(2)
    
    res = await redis_client.ft(INDEX_NAME).search(q, query_params={"vec": embedding_bytes})
    if res.docs:
        doc = res.docs[0]
        # Cosine distance is returned by score. Similarity = 1 - distance
        similarity = 1.0 - float(doc.score)
        if similarity >= threshold:
            return doc.response
    return None

async def save_to_cache(embedding: list[float], response_text: str, ttl: int):
    embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
    import uuid
    key = f"prompt:{uuid.uuid4()}"
    # hset expects bytes or strings mapping
    await redis_client.hset(key, mapping={
        b"response": response_text.encode('utf-8'),
        b"embedding": embedding_bytes
    })
    await redis_client.expire(key, ttl)
