import tiktoken
from app.config import yaml_config

def get_model_tier(prompt: str) -> str:
    rules = yaml_config.get("routing_rules", [])
    
    # Tiktoken for rough estimate
    encoding = tiktoken.get_encoding("cl100k_base")
    token_count = len(encoding.encode(prompt))
    
    for rule in rules:
        if rule.get("condition") == "contains_keyword":
            keywords = rule.get("keywords", [])
            if any(kw.lower() in prompt.lower() for kw in keywords):
                return rule.get("target_tier")
        elif rule.get("condition") == "max_tokens_exceeded":
            if token_count > rule.get("threshold", 1000):
                return rule.get("target_tier")
        elif rule.get("condition") == "catch_all":
            return rule.get("target_tier")
    
    return "low_tier"

def get_model_name(tier: str) -> str:
    return yaml_config.get("models", {}).get(tier, "groq/llama3-8b-8192")
