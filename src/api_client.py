"""
api_client.py
AI Inference Layer.

Primary:  Cerebras (fast inference, llama models)
Fallback: Gemini (google-genai)

Public API:
    generate_text(prompt, max_tokens, temperature) -> str

The prompt passed in is the fully-combined system + user message string
built by resume_generator.py.
"""

import time
import logging
from typing import Optional

from src.config import config
from src.utils import get_logger

logger = get_logger()

_cerebras_client = None
_genai_client = None


# ── Client initialisation ─────────────────────────────────────────────────────

def _get_cerebras_client():
    global _cerebras_client
    if _cerebras_client is None:
        try:
            from cerebras.cloud.sdk import Cerebras
        except ImportError:
            raise ImportError(
                "cerebras-cloud-sdk not installed. Run: pip install cerebras-cloud-sdk"
            )
        _cerebras_client = Cerebras(api_key=config.cerebras_api_key)
        logger.info("Cerebras client initialised.")
    return _cerebras_client


def _get_genai_client():
    global _genai_client
    if _genai_client is None:
        try:
            from google import genai
        except ImportError:
            raise ImportError(
                "google-genai not installed. Run: pip install google-genai"
            )
        _genai_client = genai.Client(api_key=config.gemini_api_key)
        logger.info("Gemini client initialised (model: %s).", config.gemini_model)
    return _genai_client


# ── Cerebras inference ────────────────────────────────────────────────────────

def _try_cerebras(prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
    """
    Try Cerebras with configured model then known fallbacks.
    Returns response text, or None if all models fail.
    """
    models = []
    if config.cerebras_model:
        models.append(config.cerebras_model)
    for fallback in ["llama-3.3-70b", "llama-3.1-70b", "llama-3.1-8b"]:
        if fallback not in models:
            models.append(fallback)

    for model in models:
        try:
            client = _get_cerebras_client()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise resume tailoring assistant. "
                            "Return ONLY valid JSON. No other text."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content
            if content and content.strip():
                logger.info("Cerebras succeeded with model: %s", model)
                return content.strip()
        except Exception as e:
            logger.warning("Cerebras model '%s' failed: %s", model, e)
            time.sleep(0.5)

    logger.error("All Cerebras models failed.")
    return None


# ── Gemini inference ──────────────────────────────────────────────────────────

def _try_gemini(prompt: str, max_tokens: int, temperature: float) -> str:
    """Call Gemini. Raises RuntimeError on failure."""
    try:
        from google.genai.types import GenerateContentConfig
        client = _get_genai_client()
        resp = client.models.generate_content(
            model=config.gemini_model,
            contents=prompt,
            config=GenerateContentConfig(
                system_instruction=(
                    "You are a precise resume tailoring assistant. "
                    "Return ONLY valid JSON. No other text."
                ),
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )
        content = resp.text
        if content and content.strip():
            logger.info("Gemini succeeded with model: %s", config.gemini_model)
            return content.strip()
        raise ValueError("Gemini returned an empty response.")
    except Exception as e:
        logger.error("Gemini call failed: %s", e)
        raise RuntimeError(f"Gemini inference failed: {e}") from e


# ── Public API ────────────────────────────────────────────────────────────────

def generate_text(
    prompt: str,
    max_tokens: int = 2000,
    temperature: float = 0.3,
) -> str:
    """
    Generate text using Cerebras (primary) → Gemini (fallback).

    Args:
        prompt:      Combined system + user prompt string.
        max_tokens:  Maximum output tokens. Default 2000 (enough for full resume JSON).
        temperature: Sampling temperature. 0.3 = focused, less hallucination.

    Returns:
        Raw LLM response text (JSON string expected).

    Raises:
        RuntimeError: If both Cerebras and Gemini fail.
    """
    # Phase 1: Cerebras
    if config.cerebras_api_key:
        result = _try_cerebras(prompt, max_tokens, temperature)
        if result:
            return result
        logger.warning("Cerebras unavailable — falling back to Gemini.")
    else:
        logger.info("No CEREBRAS_API_KEY — using Gemini directly.")

    # Phase 2: Gemini fallback
    if config.gemini_api_key:
        return _try_gemini(prompt, max_tokens, temperature)

    raise RuntimeError(
        "No LLM available. Set CEREBRAS_API_KEY and/or GEMINI_API_KEY in .env"
    )


# ── Legacy class wrapper (kept for compatibility) ─────────────────────────────

class LLMClient:
    def __init__(self, cfg=None):
        pass

    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> str:
        return generate_text(prompt, max_tokens, temperature)
