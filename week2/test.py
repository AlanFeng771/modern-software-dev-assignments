import os

# Must be set BEFORE importing ollama/extract, since ollama's module-level
# `chat` binds to a client created at import time using this env var.
os.environ["OLLAMA_HOST"] = "http://127.0.0.1:1"

from week2.app.services.extract import LLMServiceError, extract_action_items_llm

try:
    result = extract_action_items_llm("- do the thing")
    print("NO ERROR RAISED (unexpected):", result)
except LLMServiceError as e:
    print("Caught LLMServiceError as expected:", e)
