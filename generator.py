"""
Strategy Generator — Chutes AI / OpenAI integration with validation and regeneration.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from openai import OpenAI

from prompt import V5_SYSTEM_PROMPT
from parser import build_user_prompt, parse_strategy_description
from validator import validate_pinescript_v5

logger = logging.getLogger(__name__)

# Chutes AI — OpenAI-compatible public inference API (llm.chutes.ai)
CHUTES_BASE_URL = "https://llm.chutes.ai/v1"


def extract_code_from_response(response_text: str) -> str:
    """Extract PineScript code from GPT response (handles JSON or raw code)."""
    text = response_text.strip()
    # Try JSON first (structured output)
    if text.startswith("{"):
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data.get("code", data.get("pinescript", str(data))).strip()
            if isinstance(data, str):
                return data.strip()
        except json.JSONDecodeError:
            pass
    # Remove markdown code blocks if present
    if "```pine" in text or "```pinescript" in text:
        import re
        match = re.search(r"```(?:pine|pinescript)?\s*\n([\s\S]*?)```", text)
        if match:
            return match.group(1).strip()
    if text.startswith("```"):
        lines = text.split("\n")
        out = []
        in_block = False
        for line in lines:
            if line.strip().startswith("```"):
                in_block = not in_block
                if in_block:
                    continue
                else:
                    break
            if in_block:
                out.append(line)
        if out:
            return "\n".join(out).strip()
    return text


def _create_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    use_chutes: bool = False,
) -> OpenAI:
    """Create OpenAI-compatible client (Chutes or OpenAI)."""
    key = api_key or os.getenv("CHUTES_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("Set CHUTES_API_KEY or OPENAI_API_KEY in .env")
    if use_chutes or os.getenv("CHUTES_API_KEY"):
        return OpenAI(
            api_key=key,
            base_url=base_url or os.getenv("CHUTES_BASE_URL") or CHUTES_BASE_URL,
        )
    return OpenAI(api_key=key)


def generate_strategy(
    description: str,
    *,
    client: Optional[OpenAI] = None,
    model: str = "gpt-4o",
    temperature: float = 0.2,
    max_tokens: int = 2048,
    structured_output: bool = True,
    validation_enabled: bool = True,
    max_regeneration_attempts: int = 2,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    use_chutes: Optional[bool] = None,
) -> tuple[str, bool]:
    """
    Generate PineScript V5 strategy from plain English.
    Returns (code, validation_passed).
    Uses Chutes AI when CHUTES_API_KEY is set, otherwise OpenAI.
    """
    if client is None:
        use = use_chutes if use_chutes is not None else bool(os.getenv("CHUTES_API_KEY"))
        client = _create_client(api_key=api_key, base_url=base_url, use_chutes=use)

    user_prompt = build_user_prompt(description)

    if structured_output:
        user_prompt += "\n\nRespond with JSON: {\"code\": \"<your pinescript v5 code here>\"}"

    messages = [
        {"role": "system", "content": V5_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    last_code = ""
    last_errors: list[str] = []

    for attempt in range(max_regeneration_attempts + 1):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        code = extract_code_from_response(content)
        last_code = code

        if not validation_enabled:
            return code, True

        valid, errors = validate_pinescript_v5(code)
        last_errors = errors

        if valid:
            return code, True

        logger.warning("Validation attempt %d failed: %s", attempt + 1, errors)
        if attempt < max_regeneration_attempts:
            correction = f"Your previous output had these issues:\n" + "\n".join(f"- {e}" for e in errors)
            correction += "\n\nPlease fix the code and output the corrected PineScript V5 only."
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": correction})

    return last_code, False
