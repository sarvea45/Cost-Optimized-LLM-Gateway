import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.main import app
from litellm import exceptions

class MockResponse:
    def __init__(self, content):
        self.choices = [type('Choice', (), {'message': type('Message', (), {'content': content})})()]
        self.usage = type('Usage', (), {'prompt_tokens': 10, 'completion_tokens': 10})()
        self.data = [{"embedding": [0.01] * 1536}]
        self.model = "mock-model"
        
    def dict(self):
        return {}

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.asyncio
@patch('app.core.orchestrator.completion_cost', return_value=0.01)
@patch('app.api.endpoints.completion_cost', return_value=0.001)
@patch('app.core.orchestrator.acompletion')
@patch('app.api.endpoints.acompletion')
@patch('app.api.endpoints.check_cache', return_value=None)
@patch('app.api.endpoints.save_to_cache')
async def test_fallback_mechanism(mock_save, mock_check, mock_end_acompletion, mock_orch_acompletion, mock_cost1, mock_cost2):
    mock_end_acompletion.return_value = MockResponse("embedding")
    
    # Simulate RateLimitError on first try, then success on backup
    mock_orch_acompletion.side_effect = [
        exceptions.RateLimitError("Rate limited", response=None, llm_provider=""),
        MockResponse("Backup response")
    ]
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/v1/completions", json={
            "prompt": "Test fallback",
            "user_id": "test_user"
        })
        
    assert response.status_code == 200
    data = response.json()
    assert data["model_used"] != "gpt-4o"
    assert data["cache_hit"] is False
