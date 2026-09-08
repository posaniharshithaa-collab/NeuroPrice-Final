"""
NeuroPrice — Gemini Orchestration & Retry Policy (Phase 2, Step 3)

LOCKED POLICY:
  - Maximum 2 Gemini attempts per analysis.
  - Attempt 1: the standard structured prompt.
  - Attempt 2 (only if attempt 1 fails validation): a constrained repair
    prompt containing the exact validation failure reason.
  - BOTH attempts go through the full pipeline: JSON parse -> schema
    validation -> evidence validation. There is no code path where a
    second-attempt response skips validation because it "looks fine."
  - If attempt 2 also fails, return a controlled AnalysisFailure. No
    partial, best-effort, or averaged psychology object is ever produced.
    A failure here means the pricing engine is never called.

This module has no dependency on any real Gemini SDK -- it takes a
`gemini_client` object with a single method `generate(prompt: str) -> str`
so it can be tested with a fake client and swapped for the real one later
without touching this logic at all.
"""

import json
from dataclasses import dataclass
from typing import Protocol

from psychology_schema import parse_and_validate_schema, SchemaValidationError
from evidence_validation import validate_evidence, EvidenceValidationError, ValidatedPsychology
from psychology_prompt import build_initial_prompt, build_repair_prompt

MAX_ATTEMPTS = 2


class GeminiClient(Protocol):
    def generate(self, prompt: str) -> str: ...


@dataclass
class AnalysisSuccess:
    psychology: ValidatedPsychology
    attempts_used: int


@dataclass
class AnalysisFailure:
    message: str
    attempts_used: int
    last_error: str


def _try_parse_and_validate(raw_text: str, marketing_copy: str) -> ValidatedPsychology:
    """Runs the full pipeline for one attempt. Raises on ANY failure --
    the caller decides what to do next. This function never repairs,
    guesses, or partially accepts anything."""
    raw_json = json.loads(raw_text)  # json.JSONDecodeError on malformed JSON
    parsed = parse_and_validate_schema(raw_json)  # SchemaValidationError
    validated = validate_evidence(parsed, marketing_copy)  # EvidenceValidationError
    return validated


def analyze_marketing_copy(marketing_copy: str, gemini_client: GeminiClient) -> AnalysisSuccess | AnalysisFailure:
    last_error_message = ""

    for attempt_number in range(1, MAX_ATTEMPTS + 1):
        if attempt_number == 1:
            prompt = build_initial_prompt(marketing_copy)
        else:
            prompt = build_repair_prompt(marketing_copy, last_error_message)

        raw_text = gemini_client.generate(prompt)

        try:
            validated = _try_parse_and_validate(raw_text, marketing_copy)
            return AnalysisSuccess(psychology=validated, attempts_used=attempt_number)

        except json.JSONDecodeError as e:
            last_error_message = f"JSONDecodeError: response was not valid JSON ({e})"
        except SchemaValidationError as e:
            last_error_message = f"SchemaValidationError: {e.reason}"
        except EvidenceValidationError as e:
            last_error_message = f"EvidenceValidationError: {e.reason}"

        # Falls through to the next loop iteration (attempt 2) ONLY if
        # attempt_number < MAX_ATTEMPTS. On the last attempt, the loop
        # ends and we fall through to the controlled failure below.

    return AnalysisFailure(
        message=(
            "Psychology analysis unavailable. The AI response could not satisfy "
            "NeuroPrice's evidence and schema requirements. No financial "
            "calculation was performed."
        ),
        attempts_used=MAX_ATTEMPTS,
        last_error=last_error_message,
    )
