import pytest
from orchestrator import analyze_marketing_copy, AnalysisSuccess, AnalysisFailure, MAX_ATTEMPTS

COPY = "Only 5 seats remaining! Join 50,000+ customers. Offer ends tonight."

VALID_RESPONSE = """{
  "psychology": {"scarcity": 8, "social_proof": 7, "authority": 0,
                  "reciprocity": 0, "liking": 0, "commitment_consistency": 0},
  "evidence": [
    {"trigger": "scarcity", "reason": "Only 5 seats remaining"},
    {"trigger": "social_proof", "reason": "Join 50,000+ customers"}
  ]
}"""

MALFORMED_JSON_RESPONSE = '{"psychology": {"scarcity": 8, "social_proof"'  # truncated

MISSING_EVIDENCE_RESPONSE = """{
  "psychology": {"scarcity": 8, "social_proof": 0, "authority": 0,
                  "reciprocity": 0, "liking": 0, "commitment_consistency": 0},
  "evidence": []
}"""


class FakeGeminiClient:
    """Returns canned responses in sequence, one per call. Also records
    every prompt it was given, so tests can assert the repair prompt
    actually contains the failure reason."""
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.prompts_received: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts_received.append(prompt)
        if not self._responses:
            raise RuntimeError("FakeGeminiClient ran out of canned responses")
        return self._responses.pop(0)


# ---------------------------------------------------------------------------

def test_success_on_first_attempt_uses_exactly_one_call():
    client = FakeGeminiClient([VALID_RESPONSE])
    result = analyze_marketing_copy(COPY, client)

    assert isinstance(result, AnalysisSuccess)
    assert result.attempts_used == 1
    assert len(client.prompts_received) == 1
    assert result.psychology.scores["scarcity"] == 8


def test_recovery_on_second_attempt_after_malformed_json():
    client = FakeGeminiClient([MALFORMED_JSON_RESPONSE, VALID_RESPONSE])
    result = analyze_marketing_copy(COPY, client)

    assert isinstance(result, AnalysisSuccess)
    assert result.attempts_used == 2
    assert len(client.prompts_received) == 2
    # The second prompt must actually contain the failure reason, not just
    # be a blind repeat of the first prompt.
    assert "JSONDecodeError" in client.prompts_received[1]


def test_recovery_on_second_attempt_after_missing_evidence():
    client = FakeGeminiClient([MISSING_EVIDENCE_RESPONSE, VALID_RESPONSE])
    result = analyze_marketing_copy(COPY, client)

    assert isinstance(result, AnalysisSuccess)
    assert result.attempts_used == 2
    assert "EvidenceValidationError" in client.prompts_received[1]
    assert "no supporting evidence" in client.prompts_received[1]


def test_controlled_failure_after_both_attempts_fail():
    client = FakeGeminiClient([MALFORMED_JSON_RESPONSE, MISSING_EVIDENCE_RESPONSE])
    result = analyze_marketing_copy(COPY, client)

    assert isinstance(result, AnalysisFailure)
    assert result.attempts_used == MAX_ATTEMPTS
    assert len(client.prompts_received) == 2
    assert "No financial calculation was performed" in result.message
    assert "EvidenceValidationError" in result.last_error  # the LAST failure, attempt 2's


def test_never_exceeds_two_attempts_even_when_both_fail():
    client = FakeGeminiClient([MALFORMED_JSON_RESPONSE, MALFORMED_JSON_RESPONSE])
    analyze_marketing_copy(COPY, client)
    # If this were 3, FakeGeminiClient would have raised RuntimeError
    # ("ran out of canned responses") and the test itself would have failed.
    assert len(client.prompts_received) == 2


def test_second_attempt_response_still_goes_through_full_validation():
    """The critical rule: attempt 2 does NOT get a free pass. Feed it a
    SECOND malformed response and confirm it's rejected exactly like
    attempt 1 would have been -- no special-casing for 'last attempt.'"""
    client = FakeGeminiClient([MALFORMED_JSON_RESPONSE, MISSING_EVIDENCE_RESPONSE])
    result = analyze_marketing_copy(COPY, client)

    assert isinstance(result, AnalysisFailure)
    # If attempt 2 had bypassed validation, this would incorrectly be
    # AnalysisSuccess with an unvalidated psychology object -- it must not be.


def test_failure_never_produces_a_partial_psychology_object():
    """There must be no code path where AnalysisFailure carries a
    partially-validated psychology object. It should simply not exist
    on that branch."""
    client = FakeGeminiClient([MALFORMED_JSON_RESPONSE, MISSING_EVIDENCE_RESPONSE])
    result = analyze_marketing_copy(COPY, client)

    assert not hasattr(result, "psychology")


def test_repair_prompt_forbids_inventing_new_evidence():
    client = FakeGeminiClient([MISSING_EVIDENCE_RESPONSE, VALID_RESPONSE])
    analyze_marketing_copy(COPY, client)

    repair_prompt = client.prompts_received[1]
    assert "Do not add new unsupported evidence" in repair_prompt
