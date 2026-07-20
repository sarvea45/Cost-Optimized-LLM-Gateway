from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class GatewayRequest(BaseModel):
    prompt: str = Field(..., description="The user's input prompt")
    user_id: str = Field(..., description="Identifier for the user making the request")
    max_tokens: Optional[int] = 500
    metadata: Optional[Dict[str, Any]] = None

class GatewayResponse(BaseModel):
    response: str
    model_used: str
    cache_hit: bool
    cost_usd: float

class AnalyticsSummaryResponse(BaseModel):
    total_cost_usd: float
    total_requests: int
    average_latency_ms: float
    cache_hit_rate_percentage: float
