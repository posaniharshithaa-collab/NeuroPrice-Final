"""
NeuroPrice — Evidence Validation (Phase 2, Step 2)

Runs AFTER schema validation. Schema validation asks "is this shaped
correctly?" Evidence validation asks "is this shaped correctly AND
actually justified?" Three independent checks, each can fail on its own:

  1. COMPLETENESS  — every trigger with score > 0 has >=1 matching
                      evidence entry. (The core rule from the spec.)
  2. PLAUSIBILITY   — an evidence item's `reason` text contains at least
                      one keyword associated with the trigger it claims
                      to support. Catches "evidence for the wrong trigger"
                      (e.g. reason talks about scarcity, tagged as authority).
  3. GROUNDING       — an evidence item's `reason` text must share real
                      overlap with the actual marketing copy. Catches
                      hallucinated evidence that doesn't reference
                      anything actually in the input.

All three are heuristic, not proof of truth -- and that's stated
explicitly, not hidden. They catch the sloppy and the obviously
fabricated. They will not catch a sophisticated hallucination that
mimics the right vocabulary. That limitation belongs in the README,
not swept under the rug.

A failure anywhere means REJECT. No silent repair, no auto-zeroing of
the offending trigger. The caller decides whether to retry or surface
an analysis error.
"""

import re
from dataclasses import dataclass
from psychology_schema import RawPsychologyResponse, TRIGGERS, EvidenceItem


class EvidenceValidationError(Exception):
    def __init__(self, reason: str, details: dict | None = None):
        self.reason = reason
        self.details = details or {}
        super().__init__(reason)


# Heuristic keyword sets per trigger -- deliberately small and literal.
# Not a sentiment model. Documented as a known limitation.
TRIGGER_KEYWORDS: dict[str, set[str]] = {
    "scarcity": {"limited", "left", "remaining", "only", "few", "last", "ends",
                 "hurry", "running out", "sold out", "while supplies last", "today only"},
    "social_proof": {"customers", "users", "join", "people", "reviews", "rated",
                      "trusted by", "bestseller", "million", "thousand", "5-star", "loved by"},
    "authority": {"expert", "certified", "official", "doctor", "recommended",
                  "award", "verified", "professional", "endorsed", "licensed"},
    "reciprocity": {"free", "gift", "bonus", "complimentary", "no cost", "on us", "included"},
    "liking": {"love", "beautiful", "friendly", "delightful", "favorite", "adore", "charming"},
    "commitment_consistency": {"subscribe", "pledge", "commit", "join now", "sign up",
                                "membership", "as a member", "renew", "continue"},
}

MIN_GROUNDING_OVERLAP_TOKENS = 1  # at least one non-trivial word must appear in the source copy


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", text.lower()))


_STOPWORDS = {"the", "a", "an", "is", "are", "this", "that", "it", "and", "or",
              "to", "of", "in", "on", "for", "with", "as", "at", "by"}


def _content_tokens(text: str) -> set[str]:
    return _tokenize(text) - _STOPWORDS


@dataclass(frozen=True)
class ValidatedPsychology:
    scores: dict[str, int]
    composite_score: float
    dominant_triggers: list[str]
    evidence: list[EvidenceItem]


def validate_evidence(parsed: RawPsychologyResponse, marketing_copy: str) -> ValidatedPsychology:
    evidence_by_trigger: dict[str, list[EvidenceItem]] = {t: [] for t in TRIGGERS}
    for item in parsed.evidence:
        evidence_by_trigger[item.trigger].append(item)

    # --- Check 1: COMPLETENESS ---
    for trigger, score in parsed.scores.items():
        if score > 0 and not evidence_by_trigger[trigger]:
            raise EvidenceValidationError(
                f"Trigger '{trigger}' scored {score} but has no supporting evidence",
                {"trigger": trigger, "score": score},
            )

    copy_content_tokens = _content_tokens(marketing_copy)

    for item in parsed.evidence:
        reason_lower = item.reason.lower()

        # --- Check 2: PLAUSIBILITY (right trigger, right vocabulary) ---
        keywords = TRIGGER_KEYWORDS[item.trigger]
        if not any(kw in reason_lower for kw in keywords):
            raise EvidenceValidationError(
                f"Evidence for '{item.trigger}' does not contain any keyword "
                f"associated with that trigger -- possible mismatched trigger tag",
                {"trigger": item.trigger, "reason": item.reason},
            )

        # --- Check 3: GROUNDING (evidence must reference the actual copy) ---
        reason_content_tokens = _content_tokens(item.reason)
        overlap = reason_content_tokens & copy_content_tokens
        if len(overlap) < MIN_GROUNDING_OVERLAP_TOKENS:
            raise EvidenceValidationError(
                f"Evidence for '{item.trigger}' shares no words with the source "
                f"marketing copy -- likely hallucinated",
                {"trigger": item.trigger, "reason": item.reason, "copy": marketing_copy},
            )

    composite = round(sum(parsed.scores.values()) / len(TRIGGERS), 2)
    max_score = max(parsed.scores.values())
    dominant = [t for t, s in parsed.scores.items() if s == max_score and s > 0]

    return ValidatedPsychology(
        scores=dict(parsed.scores),
        composite_score=composite,
        dominant_triggers=dominant,
        evidence=list(parsed.evidence),
    )
