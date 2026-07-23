import asyncio
import os
from litellm import aembedding
from dotenv import load_dotenv

load_dotenv()

async def test_embed():
    try:
        print("Testing gemini/gemini-embedding-2")
        res1 = await aembedding(model="gemini/gemini-embedding-2", input=["Hello world"])
        print("002 success:", res1.data[0]['embedding'][:5])
    except Exception as e:
        print("002 failed:", e)

if __name__ == "__main__":
    asyncio.run(test_embed())
