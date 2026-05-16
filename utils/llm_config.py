"""
Single LLM configuration for the whole app (CrewAI / LiteLLM).

Set exactly one provider in .env:
  LLM_PROVIDER=ollama   → OLLAMA_MODEL, OLLAMA_BASE_URL
  LLM_PROVIDER=gemini   → GOOGLE_API_KEY, GEMINI_MODEL

No mixing: when provider is ollama, Gemini keys are not used for agents (and vice versa).
"""

from __future__ import annotations

import logging
import os
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

Provider = Literal["ollama", "gemini"]

_raw_provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
if _raw_provider == "local":
    _raw_provider = "ollama"

LLM_PROVIDER: Provider
if _raw_provider == "ollama":
    LLM_PROVIDER = "ollama"
elif _raw_provider == "gemini":
    LLM_PROVIDER = "gemini"
else:
    raise ValueError(
        f"Invalid LLM_PROVIDER={_raw_provider!r}. Use exactly one of: ollama, gemini"
    )

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()


def _normalize_gemini_model(raw: str) -> str:
    value = (raw or "gemini-2.5-flash-lite").strip()
    if value.startswith("GEMINI_MODEL="):
        value = value.split("=", 1)[1].strip()
    return value or "gemini-2.5-flash-lite"


GEMINI_MODEL = _normalize_gemini_model(os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"))

# Set once at import: LiteLLM/CrewAI model string for all agents
CREW_LLM_MODEL: str


def _resolve_crew_llm_model() -> str:
    if LLM_PROVIDER == "ollama":
        if not OLLAMA_MODEL:
            raise ValueError("OLLAMA_MODEL is empty. Example: qwen2.5:3b")
        os.environ["OLLAMA_API_BASE"] = OLLAMA_BASE_URL
        model = f"ollama/{OLLAMA_MODEL}"
        logger.info("LLM provider: ollama | model=%s | base=%s", OLLAMA_MODEL, OLLAMA_BASE_URL)
        return model

    if not GOOGLE_API_KEY:
        raise ValueError(
            "LLM_PROVIDER=gemini requires GOOGLE_API_KEY in .env. "
            "Or set LLM_PROVIDER=ollama for local Ollama."
        )
    os.environ["GEMINI_API_KEY"] = GOOGLE_API_KEY
    model = f"gemini/{GEMINI_MODEL}"
    logger.info("LLM provider: gemini | model=%s", GEMINI_MODEL)
    return model


CREW_LLM_MODEL = _resolve_crew_llm_model()


def get_crew_llm_model() -> str:
    """LiteLLM provider string used by every CrewAI agent."""
    return CREW_LLM_MODEL


def is_ollama() -> bool:
    return LLM_PROVIDER == "ollama"


def is_gemini() -> bool:
    return LLM_PROVIDER == "gemini"
