from app.core.router import get_model_tier, get_model_name
from unittest.mock import patch

@patch('app.core.router.yaml_config', {
    "routing_rules": [
        {"name": "complex", "condition": "contains_keyword", "keywords": ["analyze"], "target_tier": "high_tier"},
        {"name": "long", "condition": "max_tokens_exceeded", "threshold": 10, "target_tier": "mid_tier"},
        {"name": "default", "condition": "catch_all", "target_tier": "low_tier"}
    ],
    "models": {
        "high_tier": "model-high",
        "mid_tier": "model-mid",
        "low_tier": "model-low"
    }
})
def test_router_logic():
    # Keyword match
    assert get_model_tier("Please analyze this") == "high_tier"
    assert get_model_name("high_tier") == "model-high"
    
    # Token count match
    assert get_model_tier("This is a very long prompt that exceeds ten tokens for sure") == "mid_tier"
    
    # Default fallback
    assert get_model_tier("Short prompt") == "low_tier"
