import os
import pytest
from ollama import ResponseError

from ..app.services import extract
from ..app.services.extract import LLMServiceError, extract_action_items, extract_action_items_llm


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


# TODO 2: tests for extract_action_items_llm(). These call the local Ollama
# model directly (no mocking), so assertions check for expected content via
# substring matching rather than exact strings, since LLM phrasing can vary.


def test_extract_llm_bullet_list():
    text = """
    Meeting notes:
    - Set up the database
    - Implement the API extract endpoint
    We discussed the roadmap for next quarter.
    """.strip()

    items = extract_action_items_llm(text)
    joined = " ".join(items).lower()
    assert len(items) >= 2
    assert "database" in joined
    assert "endpoint" in joined
    assert "roadmap" not in joined


def test_extract_llm_keyword_prefixed_lines():
    text = """
    TODO: write unit tests for the extractor
    Action: review the pull request
    Next: schedule the demo with the team
    """.strip()

    items = extract_action_items_llm(text)
    joined = " ".join(items).lower()
    assert len(items) >= 2
    assert "test" in joined
    assert "review" in joined or "pull request" in joined


def test_extract_llm_empty_input():
    assert extract_action_items_llm("") == []
    assert extract_action_items_llm("   \n  ") == []


# The two tests below cover the "Ollama unreachable / errored" path, which
# can't be triggered by calling the real local service, so ollama.chat is
# monkeypatched to simulate the failure.


def test_extract_llm_connection_error_raises_llm_service_error(monkeypatch):
    def fake_chat(*args, **kwargs):
        raise ConnectionError("Failed to connect to Ollama.")

    monkeypatch.setattr(extract, "chat", fake_chat)

    with pytest.raises(LLMServiceError):
        extract_action_items_llm("- do the thing")


def test_extract_llm_response_error_raises_llm_service_error(monkeypatch):
    def fake_chat(*args, **kwargs):
        raise ResponseError("model not found", 404)

    monkeypatch.setattr(extract, "chat", fake_chat)

    with pytest.raises(LLMServiceError):
        extract_action_items_llm("- do the thing")
