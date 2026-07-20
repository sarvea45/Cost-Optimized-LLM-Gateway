import os
import yaml
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/gateway"
    redis_url: str = "redis://localhost:6379/0"
    
    # API Keys (loaded from env)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

def load_yaml_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

settings = Settings()
yaml_config = load_yaml_config()
