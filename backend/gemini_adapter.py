"""
NeuroPrice — Real Gemini Adapter (Phase 2, Step: Real Adapter)

This is the ONLY file in the whole system that talks to the actual
Gemini API. It implements the same `GeminiClient` Protocol
(`.generate(prompt: str) -> str`) that FakeGeminiClient implements in
the test suite -- which is why orchestrator.py needed zero changes to
support this. That isolation was the entire point of using a Protocol
instead of importing a specific SDK type directly into orchestrator.py.

REQUIRES: `pip install google-genai --break-system-packages` and a
GEMINI_API_KEY environment variable. This adapter cannot be exercised
inside this sandbox (no network route to the Gemini API here) -- it's
built and structurally reviewable now, and becomes testable the moment
you run it somewhere with real network access and a key.
"""

import os
from google import genai
from google.genai import types


class GeminiAdapterConfigError(Exception):
    """Raised at construction time if the environment isn't set up --
    fails loudly and immediately, not on the first .generate() call
    buried inside a retry loop."""
    pass


class RealGeminiClient:
    def __init__(self, model: str = "gemini-2.0-flash", api_key: str | None = None):
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not resolved_key:
            raise GeminiAdapterConfigError(
                "GEMINI_API_KEY not set. Pass api_key= explicitly or set the env var."
            )
        self._client = genai.Client(api_key=resolved_key)
        self._model = model

    def generate(self, prompt: str) -> str:
        """Returns raw text. Deliberately does NOT parse or validate here
        -- that stays the orchestrator's job, so this file has exactly
        one responsibility: get text back from Gemini.

        response_mime_type='application/json' asks Gemini to skip markdown
        code fences, which reduces (but does not eliminate) the odds of a
        JSONDecodeError on the validator's end -- the validator remains the
        authority regardless of what this returns.
        """
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,  # low but nonzero -- this is classification, not creative writing
            ),
        )
        return response.text
