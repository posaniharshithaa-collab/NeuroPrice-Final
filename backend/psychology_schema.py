"""
NeuroPrice — Psychology Output Schema (Phase 2, Step 1)

This is the CONTRACT Gemini's raw response must satisfy before it's even
handed to evidence validation. Schema validation catches structural
problems (wrong types, out-of-range scores, malformed JSON). Evidence
validation (separate module) catches semantic problems (a score with no
justification, or justification for the wrong trigger).

Deliberately using plain dataclasses + manual checks instead of a
library like pydantic, so every rule is visible in one file and nothing
is hidden behind decorator magic -- easy to defend line by line.
"""

from dataclasses import dataclass

TRIGGERS = (
    "scarcity",
    "social_proof",
    "authority",
    "reciprocity",
    "liking",
    "commitment_consistency",
)

SCORE_MIN = 0
SCORE_MAX = 10


class SchemaValidationError(Exception):
    """Raised when Gemini's raw JSON fails structural validation.
    This is a HARD rejection -- no partial repair, no silent clamping."""
    def __init__(self, reason: str, raw: dict | None = None):
        self.reason = reason
        self.raw = raw
        super().__init__(reason)


@dataclass(frozen=True)
class EvidenceItem:
    trigger: str
    reason: str


@dataclass(frozen=True)
class RawPsychologyResponse:
    """The shape we require directly out of JSON parsing, before any
    semantic checks. Every field here must be present in Gemini's output."""
    scores: dict[str, int]
    evidence: list[EvidenceItem]


def parse_and_validate_schema(raw_json: dict) -> RawPsychologyResponse:
    """Structural validation only. Raises SchemaValidationError on any
    violation. Does NOT check score/evidence consistency -- that's the
    evidence validator's job, kept separate on purpose."""

    if not isinstance(raw_json, dict):
        raise SchemaValidationError("Top-level response is not a JSON object", raw_json)

    if "psychology" not in raw_json:
        raise SchemaValidationError("Missing top-level 'psychology' key", raw_json)

    psych = raw_json["psychology"]
    if not isinstance(psych, dict):
        raise SchemaValidationError("'psychology' must be an object", raw_json)

    # --- scores: every trigger must be present, exactly once, as an int in range ---
    missing = [t for t in TRIGGERS if t not in psych]
    if missing:
        raise SchemaValidationError(f"Missing required trigger(s): {missing}", raw_json)

    unexpected = [k for k in psych if k not in TRIGGERS]
    if unexpected:
        raise SchemaValidationError(f"Unexpected key(s) in psychology object: {unexpected}", raw_json)

    scores: dict[str, int] = {}
    for trigger in TRIGGERS:
        value = psych[trigger]
        if isinstance(value, bool) or not isinstance(value, int):
            raise SchemaValidationError(f"Score for '{trigger}' must be an integer, got {type(value).__name__}", raw_json)
        if not (SCORE_MIN <= value <= SCORE_MAX):
            raise SchemaValidationError(f"Score for '{trigger}' = {value} is outside [{SCORE_MIN}, {SCORE_MAX}]", raw_json)
        scores[trigger] = value

    # --- evidence: must be a list of {trigger, reason} objects ---
    if "evidence" not in raw_json:
        raise SchemaValidationError("Missing top-level 'evidence' key", raw_json)

    evidence_raw = raw_json["evidence"]
    if not isinstance(evidence_raw, list):
        raise SchemaValidationError("'evidence' must be a list", raw_json)

    evidence: list[EvidenceItem] = []
    for i, item in enumerate(evidence_raw):
        if not isinstance(item, dict):
            raise SchemaValidationError(f"evidence[{i}] must be an object", raw_json)
        if "trigger" not in item or "reason" not in item:
            raise SchemaValidationError(f"evidence[{i}] missing 'trigger' or 'reason'", raw_json)
        trigger = item["trigger"]
        reason = item["reason"]
        if trigger not in TRIGGERS:
            raise SchemaValidationError(f"evidence[{i}] references unknown trigger '{trigger}'", raw_json)
        if not isinstance(reason, str) or not reason.strip():
            raise SchemaValidationError(f"evidence[{i}] 'reason' must be a non-empty string", raw_json)
        evidence.append(EvidenceItem(trigger=trigger, reason=reason.strip()))

    return RawPsychologyResponse(scores=scores, evidence=evidence)
