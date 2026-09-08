"""
NeuroPrice — Real AI Adapter

The project originally used Gemini, so the existing class names are
intentionally preserved:

    RealGeminiClient
    GeminiAdapterConfigError

This keeps api.py and orchestrator.py unchanged while the actual
AI provider underneath is OpenAI.

AI responsibility:
- Read marketing copy
- Extract persuasion/psychology signals
- Return raw JSON text

The AI does NOT:
- calculate pricing
- calculate elasticity
- calculate revenue
- recommend prices
- interpret financial results

Those responsibilities remain in the NeuroPrice validator,
orchestrator, and deterministic pricing engine.

REQUIRES:
    pip install openai

ENVIRONMENT:
    OPENAI_API_KEY
"""

import os

from openai import OpenAI


class GeminiAdapterConfigError(Exception):
    """
    Raised when the AI API configuration is missing.

    The name is preserved for compatibility with the existing
    NeuroPrice application.
    """

    pass


class RealGeminiClient:
    """
    Compatibility wrapper for the existing NeuroPrice architecture.

    Despite the historical Gemini class name, this implementation
    now uses OpenAI internally.
    """

    def __init__(
        self,
        model: str = "gpt-5.6-luna",
        api_key: str | None = None,
    ):
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")

        if not resolved_key:
            raise GeminiAdapterConfigError(
                "OPENAI_API_KEY not set. "
                "Pass api_key= explicitly or set the environment variable."
            )

        self._client = OpenAI(api_key=resolved_key)
        self._model = model

    def generate(self, prompt: str) -> str:
        """
        Send the prompt to OpenAI and return raw JSON text.

        Parsing and validation deliberately happen outside this adapter.
        The validator remains the authority over whether AI output is
        trusted by the rest of the application.
        """

        response = self._client.responses.create(
            model=self._model,
            input=prompt,
            text={
                "format": {
                    "type": "json_object"
                }
            },
        )

        return response.output_text