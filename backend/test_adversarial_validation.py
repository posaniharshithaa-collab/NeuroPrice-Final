"""
Adversarial tests for the Gemini output validation pipeline.

Goal: every one of these should be REJECTED. If any of these silently
passes, the validator has a hole an LLM will eventually find on its own
(hallucination doesn't need malice -- confident wrongness is enough).
"""

import json
import pytest
from psychology_schema import parse_and_validate_schema, SchemaValidationError, TRIGGERS
from evidence_validation import validate_evidence, EvidenceValidationError

VALID_COPY = "Only 5 seats remaining! Join 50,000+ customers. Offer ends tonight."


def _base_scores(**overrides) -> dict:
    scores = {t: 0 for t in TRIGGERS}
    scores.update(overrides)
    return scores


# ---------------------------------------------------------------------------
# Schema-level adversarial cases
# ---------------------------------------------------------------------------

def test_reject_score_above_max():
    raw = {"psychology": _base_scores(scarcity=11), "evidence": []}
    with pytest.raises(SchemaValidationError, match="outside"):
        parse_and_validate_schema(raw)


def test_reject_negative_score():
    raw = {"psychology": _base_scores(scarcity=-3), "evidence": []}
    with pytest.raises(SchemaValidationError, match="outside"):
        parse_and_validate_schema(raw)


def test_reject_non_integer_score():
    raw = {"psychology": _base_scores(scarcity=7.5), "evidence": []}
    with pytest.raises(SchemaValidationError, match="integer"):
        parse_and_validate_schema(raw)


def test_reject_missing_trigger():
    scores = _base_scores()
    del scores["reciprocity"]
    raw = {"psychology": scores, "evidence": []}
    with pytest.raises(SchemaValidationError, match="Missing required trigger"):
        parse_and_validate_schema(raw)


def test_reject_extra_unexpected_trigger():
    scores = _base_scores()
    scores["fabricated_trigger"] = 5
    raw = {"psychology": scores, "evidence": []}
    with pytest.raises(SchemaValidationError, match="Unexpected key"):
        parse_and_validate_schema(raw)


def test_reject_evidence_for_unknown_trigger():
    raw = {
        "psychology": _base_scores(scarcity=8),
        "evidence": [{"trigger": "fomo", "reason": "made it up"}],
    }
    with pytest.raises(SchemaValidationError, match="unknown trigger"):
        parse_and_validate_schema(raw)


def test_reject_evidence_missing_reason_field():
    raw = {
        "psychology": _base_scores(scarcity=8),
        "evidence": [{"trigger": "scarcity"}],
    }
    with pytest.raises(SchemaValidationError, match="missing"):
        parse_and_validate_schema(raw)


def test_reject_empty_reason_string():
    raw = {
        "psychology": _base_scores(scarcity=8),
        "evidence": [{"trigger": "scarcity", "reason": "   "}],
    }
    with pytest.raises(SchemaValidationError, match="non-empty"):
        parse_and_validate_schema(raw)


def test_reject_truly_malformed_json_string_at_the_json_loads_boundary():
    # This is the "malformed JSON" adversarial case at the actual boundary:
    # Gemini's raw text output isn't even valid JSON (e.g. truncated by a
    # token limit mid-object). json.loads itself must raise -- this happens
    # BEFORE parse_and_validate_schema is ever called, and the caller is
    # responsible for catching json.JSONDecodeError as its own reject path.
    truncated_response_text = '{"psychology": {"scarcity": 8, "social_proof"'
    with pytest.raises(json.JSONDecodeError):
        json.loads(truncated_response_text)


def test_reject_malformed_top_level_not_a_dict():
    with pytest.raises(SchemaValidationError, match="not a JSON object"):
        parse_and_validate_schema(["this", "is", "a", "list", "not", "a", "dict"])


def test_reject_missing_psychology_key_entirely():
    raw = {"evidence": []}
    with pytest.raises(SchemaValidationError, match="Missing top-level 'psychology'"):
        parse_and_validate_schema(raw)


def test_reject_missing_evidence_key_entirely():
    raw = {"psychology": _base_scores()}
    with pytest.raises(SchemaValidationError, match="Missing top-level 'evidence'"):
        parse_and_validate_schema(raw)


def test_accept_well_formed_response_passes_schema():
    raw = {
        "psychology": _base_scores(scarcity=8, social_proof=7),
        "evidence": [
            {"trigger": "scarcity", "reason": "Copy says only 5 seats remaining."},
            {"trigger": "social_proof", "reason": "Copy references 50,000+ customers."},
        ],
    }
    parsed = parse_and_validate_schema(raw)
    assert parsed.scores["scarcity"] == 8
    assert len(parsed.evidence) == 2


# ---------------------------------------------------------------------------
# Evidence-level adversarial cases (require valid schema first)
# ---------------------------------------------------------------------------

def test_reject_nonzero_score_with_zero_evidence_entries():
    raw = {"psychology": _base_scores(scarcity=8), "evidence": []}
    parsed = parse_and_validate_schema(raw)
    with pytest.raises(EvidenceValidationError, match="no supporting evidence"):
        validate_evidence(parsed, VALID_COPY)


def test_reject_evidence_for_wrong_trigger_vocabulary():
    # Tagged as 'authority' but the reason text is pure scarcity language --
    # this is the "evidence for the wrong trigger" adversarial case.
    raw = {
        "psychology": _base_scores(authority=6),
        "evidence": [{"trigger": "authority", "reason": "Only 5 seats remaining, act now."}],
    }
    parsed = parse_and_validate_schema(raw)
    with pytest.raises(EvidenceValidationError, match="mismatched trigger"):
        validate_evidence(parsed, VALID_COPY)


def test_reject_hallucinated_evidence_not_in_source_copy():
    # Reason text is plausible-sounding but shares NOTHING with the actual
    # marketing copy -- Gemini invented a quote that was never there.
    raw = {
        "psychology": _base_scores(authority=7),
        "evidence": [{"trigger": "authority", "reason": "Endorsed by Dr. Smith, a certified expert in the field."}],
    }
    parsed = parse_and_validate_schema(raw)
    with pytest.raises(EvidenceValidationError, match="hallucinated"):
        validate_evidence(parsed, VALID_COPY)


def test_zero_score_trigger_requires_no_evidence():
    # Absence of evidence for a trigger that correctly scored 0 must NOT
    # raise -- only nonzero scores require evidence.
    raw = {
        "psychology": _base_scores(scarcity=8),
        "evidence": [{"trigger": "scarcity", "reason": "Only 5 seats remaining."}],
    }
    parsed = parse_and_validate_schema(raw)
    result = validate_evidence(parsed, VALID_COPY)
    assert result.scores["authority"] == 0  # untouched, no evidence needed, no error


def test_full_valid_pipeline_produces_correct_composite_and_dominant():
    raw = {
        "psychology": _base_scores(scarcity=8, social_proof=7),
        "evidence": [
            {"trigger": "scarcity", "reason": "Copy emphasizes only 5 seats remaining."},
            {"trigger": "social_proof", "reason": "Copy references 50,000+ customers already joined."},
        ],
    }
    parsed = parse_and_validate_schema(raw)
    result = validate_evidence(parsed, VALID_COPY)

    assert result.composite_score == round((8 + 7) / 6, 2)
    assert result.dominant_triggers == ["scarcity"]  # single max


def test_multiple_evidence_items_for_same_trigger_all_must_pass():
    # If Gemini gives 2 pieces of evidence for one trigger, BOTH must pass
    # plausibility/grounding -- one good reason doesn't excuse a bad one.
    raw = {
        "psychology": _base_scores(scarcity=8),
        "evidence": [
            {"trigger": "scarcity", "reason": "Only 5 seats remaining."},
            {"trigger": "scarcity", "reason": "Endorsed by a licensed doctor."},  # wrong vocabulary, hallucinated
        ],
    }
    parsed = parse_and_validate_schema(raw)
    with pytest.raises(EvidenceValidationError):
        validate_evidence(parsed, VALID_COPY)
