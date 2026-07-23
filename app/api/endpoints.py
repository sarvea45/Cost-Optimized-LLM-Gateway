from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Integer
from typing import Optional
from datetime import datetime, timezone
from app.db.database import get_db
from app.db.models import RequestLog
from app.api.schemas import GatewayRequest, GatewayResponse, AnalyticsSummaryResponse
from app.core.preprocessing import clean_prompt
from app.core.router import get_model_tier, get_model_name
from app.core.orchestrator import execute_llm_call
from app.core.cache import get_embedding, check_cache, save_to_cache
from app.config import yaml_config
from litellm import acompletion, aembedding
from litellm.utils import completion_cost

router = APIRouter(prefix="/v1")

async def log_request_to_db(
    db: AsyncSession,
    user_id: str,
    model_used: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    cost_usd: float,
    cache_hit: bool
):
    total_tokens = prompt_tokens + completion_tokens
    log_entry = RequestLog(
        user_id=user_id,
        model_used=model_used,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        cache_hit=cache_hit
    )
    db.add(log_entry)
    await db.commit()

@router.post("/completions", response_model=GatewayResponse)
async def create_completion(
    request: GatewayRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    start_time = datetime.utcnow()
    
    # 1. Preprocessing
    cleaned_prompt = clean_prompt(request.prompt)
    
    # 2. Caching Logic
    caching_config = yaml_config.get("caching", {})
    cache_enabled = caching_config.get("enabled", True)
    similarity_threshold = caching_config.get("similarity_threshold", 0.95)
    
    embedding = None
    embedding_cost = 0.0
    if cache_enabled:
        try:
            # We already have get_embedding in app.core.cache, let's use it
            embedding = await get_embedding(cleaned_prompt)
            # Calculating cost is not easily returned from get_embedding unless we modify it, 
            # so let's call acompletion directly here or modify get_embedding later. 
            # Actually I'll use it as is, and just fetch cost directly.
            embedding_model = yaml_config.get("models", {}).get("embedding", "text-embedding-3-small")
            emb_resp = await aembedding(model=embedding_model, input=cleaned_prompt)
            embedding = emb_resp.data[0]["embedding"]
            try:
                embedding_cost = completion_cost(completion_response=emb_resp, model=embedding_model) or 0.0
            except Exception:
                embedding_cost = 0.0
            
            cached_text = await check_cache(embedding, similarity_threshold)
            if cached_text:
                latency = (datetime.utcnow() - start_time).total_seconds() * 1000
                background_tasks.add_task(
                    log_request_to_db, db, request.user_id, "cache", 0, 0, latency, embedding_cost, True
                )
                return GatewayResponse(
                    response=cached_text,
                    model_used="cache",
                    cache_hit=True,
                    cost_usd=embedding_cost
                )
        except Exception as e:
            print(f"Cache check error: {e}")

    # 3. Routing
    tier = get_model_tier(cleaned_prompt)
    model_name = get_model_name(tier)
    
    # 4. Orchestration
    llm_resp, actual_model, llm_cost = await execute_llm_call(model_name, cleaned_prompt)
    response_text = llm_resp.choices[0].message.content
    
    prompt_tokens = llm_resp.usage.prompt_tokens if hasattr(llm_resp, 'usage') else 0
    completion_tokens = llm_resp.usage.completion_tokens if hasattr(llm_resp, 'usage') else 0
    
    latency = (datetime.utcnow() - start_time).total_seconds() * 1000
    total_cost = (llm_cost or 0.0) + embedding_cost
    
    if cache_enabled and embedding:
        ttl = caching_config.get("ttl_seconds", 86400)
        await save_to_cache(embedding, response_text, ttl)
        
    background_tasks.add_task(
        log_request_to_db, db, request.user_id, actual_model, prompt_tokens, completion_tokens, latency, total_cost, False
    )
    
    return GatewayResponse(
        response=response_text,
        model_used=actual_model,
        cache_hit=False,
        cost_usd=total_cost
    )

@router.get("/analytics/requests/{request_id}")
async def get_request_log(request_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RequestLog).where(RequestLog.id == request_id))
    log = result.scalars().first()
    if not log:
        raise HTTPException(status_code=404, detail="Request not found")
    return log

@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(
        func.sum(RequestLog.cost_usd).label("total_cost"),
        func.count(RequestLog.id).label("total_requests"),
        func.avg(RequestLog.latency_ms).label("avg_latency"),
        func.sum(func.cast(RequestLog.cache_hit, Integer)).label("cache_hits")
    )
    
    if start_date:
        query = query.where(RequestLog.timestamp >= start_date)
    if end_date:
        query = query.where(RequestLog.timestamp <= end_date)
        
    result = await db.execute(query)
    row = result.one()
    
    total_cost = row.total_cost or 0.0
    total_reqs = row.total_requests or 0
    avg_lat = row.avg_latency or 0.0
    hits = row.cache_hits or 0
    
    hit_rate = (hits / total_reqs * 100) if total_reqs > 0 else 0.0
    
    return AnalyticsSummaryResponse(
        total_cost_usd=total_cost,
        total_requests=total_reqs,
        average_latency_ms=avg_lat,
        cache_hit_rate_percentage=hit_rate
    )
