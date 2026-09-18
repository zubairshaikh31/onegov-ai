import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ai.services.nvidia_provider import NvidiaProvider
from ai.services.base_provider import Message


@pytest.mark.asyncio
async def test_nvidia_provider_initialization():
    provider = NvidiaProvider(api_key="test_key")
    assert provider.provider_name == "nvidia"
    assert provider.model_name == "nvidia/nemotron-3.5-lightning-30b-a3b"


@pytest.mark.asyncio
async def test_nvidia_provider_chat():
    provider = NvidiaProvider(api_key="test_key")
    
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Grounded response text."
    mock_response.choices = [mock_choice]
    
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 20
    mock_usage.total_tokens = 30
    mock_response.usage = mock_usage
    
    provider._client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    messages = [Message(role="user", content="Hello")]
    resp = await provider.chat(messages)
    
    assert resp.content == "Grounded response text."
    assert resp.input_tokens == 10
    assert resp.output_tokens == 20
    assert resp.total_tokens == 30
    assert resp.provider_used == "nvidia"


@pytest.mark.asyncio
async def test_nvidia_provider_chat_stream():
    provider = NvidiaProvider(api_key="test_key")
    
    # Mock chunks yielded by stream
    class MockChunk:
        def __init__(self, content, reasoning=None):
            self.choices = [MagicMock()]
            self.choices[0].delta = MagicMock()
            self.choices[0].delta.content = content
            self.choices[0].delta.reasoning_content = reasoning

    async def mock_generator():
        # Yield reasoning content (should be skipped)
        yield MockChunk(None, "I am reasoning.")
        # Yield normal content
        yield MockChunk("Real ", None)
        yield MockChunk("answer.", None)

    provider._client.chat.completions.create = AsyncMock(return_value=mock_generator())
    
    messages = [Message(role="user", content="Hello")]
    collected_tokens = []
    async for token in provider.chat_stream(messages):
        collected_tokens.append(token)
        
    assert collected_tokens == ["Real ", "answer."]
