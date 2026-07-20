from fastapi import FastAPI
from app.api.endpoints import router as api_router
from app.core.cache import init_redis_index
from app.db.database import engine, Base
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Cost-Optimized LLM Gateway")

@app.on_event("startup")
async def on_startup():
    # Initialize DB schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Redis Vector Index
    await init_redis_index()

app.include_router(api_router)
