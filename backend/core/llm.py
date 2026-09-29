"""Groq LLM client with retry logic."""

import json
import logging
import re
from typing import Optional

from groq import Groq

from backend.core.config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE

logger = logging.getLogger(__name__)

if not GROQ_API_KEY:
    logger.warning("No GROQ_API_KEY found in .env — LLM calls will fail.")


def _extract_json(text: str):
    """Extract JSON from LLM response, handling markdown fences and noise."""
    text = text.strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Markdown code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. First { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM response: {text[:300]}")


def get_completion(
    prompt: str,
    json_mode: bool = False,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    retries: int = 3,
) -> str:
    """Get a text completion from Groq with retry logic."""
    use_model = model or LLM_MODEL
    use_temp = temperature if temperature is not None else LLM_TEMPERATURE

    messages = [{"role": "user", "content": prompt}]
    if json_mode:
        messages.insert(0, {
            "role": "system",
            "content": (
                "You are a helpful assistant. Always respond with valid JSON "
                "only. No markdown fences, no explanation, no extra text."
            ),
        })

    last_error = None
    for attempt in range(retries):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            kwargs = {
                "model": use_model,
                "messages": messages,
                "temperature": use_temp,
                "max_tokens": 2048,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()

        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str:
                logger.warning(f"Groq API rate-limited (attempt {attempt + 1}), retrying...")
            else:
                logger.error(f"Groq API error: {e}")
                if attempt < retries - 1:
                    continue
                raise

    raise last_error or RuntimeError("Groq API request failed.")


def get_json_completion(
    prompt: str,
    model: Optional[str] = None,
    retries: int = 2,
) -> dict:
    """Get a parsed JSON response from the LLM with retry logic."""
    last_error = None
    for attempt in range(retries + 1):
        try:
            text = get_completion(prompt, json_mode=True, model=model)
            return _extract_json(text)
        except Exception as e:
            last_error = e
    if last_error is not None:
        raise last_error
    raise RuntimeError("Failed to get JSON completion: no response received")
