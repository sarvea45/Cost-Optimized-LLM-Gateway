# Cost-Optimized LLM Gateway

A production-ready, centralized LLM gateway that intelligently routes prompts, implements semantic caching, and tracks costs to scale AI applications economically.

## Features

- **Intelligent Routing**: Automatically assigns prompts to low, mid, or high-tier models based on configurable rules (keywords, token count).
- **Semantic Caching**: Uses `text-embedding-3-small` and Redis Vector Search (Cosine Similarity) to cache and retrieve responses for conceptually similar queries.
- **Automated Fallbacks**: Gracefully retries failed LLM requests (e.g., `RateLimitError`) using configured backup models via LiteLLM.
- **Granular Telemetry**: Asynchronously logs every transaction's token usage, latency, and precise USD cost to PostgreSQL.

## Prerequisites

- Docker and Docker Compose
- LLM Provider API Keys (e.g., OpenAI, Anthropic, Groq)

## Setup Instructions

1. **Clone the repository** (or navigate to the root directory).
2. **Environment Variables**:
   Copy the example environment file and add your API keys.
   ```bash
   cp .env.example .env
   # Edit .env and insert your real API keys
   ```
3. **Configuration**:
   Review or modify `config.yaml` to adjust models, caching thresholds, and routing rules.
4. **Build and Start Services**:
   ```bash
   docker-compose build
   docker-compose up -d
   ```
5. **Verify Health**:
   Ensure `api`, `postgres`, and `redis` containers are running (`docker-compose ps`).

## API Endpoints

### 1. Create Completion
Route a prompt through the gateway.

```bash
curl -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of France?",
    "user_id": "user_123"
  }'
```
**Response:**
```json
{
  "response": "The capital of France is Paris.",
  "model_used": "groq/llama3-8b-8192",
  "cache_hit": false,
  "cost_usd": 0.0001
}
```

### 2. Analytics Summary
Retrieve aggregate metrics.

```bash
curl -X GET http://localhost:8000/v1/analytics/summary
```
**Response:**
```json
{
  "total_cost_usd": 0.015,
  "total_requests": 15,
  "average_latency_ms": 1205.5,
  "cache_hit_rate_percentage": 25.0
}
```

## Running Tests

Execute the automated test suite within the Docker container:

```bash
docker-compose exec -T api pytest
```
