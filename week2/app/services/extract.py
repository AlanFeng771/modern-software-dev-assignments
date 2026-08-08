from __future__ import annotations

import re
from typing import List
from ollama import ResponseError, chat
from pydantic import BaseModel, Field, ValidationError

from .. import config


class LLMServiceError(Exception):
    """Raised when the Ollama service is unreachable or returns an error."""

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


DEFAULT_OLLAMA_MODEL = config.OLLAMA_MODEL

# Drives WHAT the model does (task); schema below drives the output shape.
LLM_SYSTEM_PROMPT = (
    "You are an assistant that parses free-form notes provided by the user "
    "and converts them into a structured list of action items."
)


# Ollama `format` schema: enforces output JSON shape via constrained decoding.
class ActionItemsResponse(BaseModel):
    action_items: List[str] = Field(
        description=(
            "Concrete, actionable tasks extracted from the notes, each phrased "
            "as a short imperative sentence (e.g. 'Set up database'). "
            "Empty list if no action items are found."
        )
    )


def extract_action_items_llm(text: str, model: str | None = None) -> List[str]:
    """LLM-powered alternative to extract_action_items(), using Ollama structured outputs."""
    stripped_text = text.strip()
    if not stripped_text:
        return []

    # Service-level failures (Ollama unreachable, model error) are distinct from
    # parse failures below: they mean "couldn't ask the model" rather than "the
    # model found nothing", so they're raised instead of swallowed to an empty list.
    try:
        response = chat(
            model=model or DEFAULT_OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": LLM_SYSTEM_PROMPT},
                {"role": "user", "content": stripped_text},
            ],
            format=ActionItemsResponse.model_json_schema(),
            options={"temperature": 0},
        )
    except (ConnectionError, ResponseError) as exc:
        raise LLMServiceError(str(exc)) from exc

    try:
        parsed = ActionItemsResponse.model_validate_json(response.message.content)
    except (ValidationError, TypeError):
        return []

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in parsed.action_items:
        cleaned = item.strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(cleaned)
    return unique


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters
