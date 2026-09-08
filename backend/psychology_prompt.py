"""
NeuroPrice — Gemini Prompt (Phase 2, Step 4)

Deliberately narrow. This prompt does NOT try to make Gemini trustworthy
through clever wording -- that's not how any of this works. Its only two
jobs are:
  1. Maximize the odds of a first-pass response that satisfies the
     validator (saves latency and API cost).
  2. Make the forbidden actions explicit, so a violation is a clear
     prompt-adherence failure, not an ambiguous judgment call.

The validator is what actually enforces correctness. This file could be
deleted and rewritten tomorrow without changing what the system is
allowed to accept.
"""

from psychology_schema import TRIGGERS

_TRIGGER_LIST = "\n".join(f"  - {t}" for t in TRIGGERS)

_SCHEMA_EXAMPLE = """{
  "psychology": {
    "scarcity": 0,
    "social_proof": 0,
    "authority": 0,
    "reciprocity": 0,
    "liking": 0,
    "commitment_consistency": 0
  },
  "evidence": [
    { "trigger": "scarcity", "reason": "short quote or paraphrase of the specific phrase that justifies this score" }
  ]
}"""

_FORBIDDEN_ACTIONS = """You are NOT allowed to, under any circumstances:
  - recommend, suggest, or imply a specific price
  - calculate or estimate price elasticity
  - calculate or estimate revenue, demand, or any financial figure
  - modify, restate, or reason about economic inputs (price, cost, conversion rate)
  - infer a customer's willingness to pay
  - make causal claims about how the copy will affect actual buyer behavior
  - invent, paraphrase-beyond-recognition, or fabricate a quote that does not appear in the copy
  - give a trigger a score above 0 without a matching evidence entry"""

_BASE_INSTRUCTIONS = f"""You are a text-classification component. Your ONLY task is to score the
marketing copy below against six persuasion triggers, based ONLY on what
the text explicitly contains.

The six triggers are:
{_TRIGGER_LIST}

For each trigger, output an integer score from 0 to 10, where 0 means the
trigger is not present at all, and 10 means the trigger is used
extremely strongly and explicitly.

RULE: If you give a trigger a score greater than 0, you MUST include at
least one entry in "evidence" for that exact trigger. The "reason" for
each evidence entry must directly reference specific words or phrases
that actually appear in the marketing copy below -- do not paraphrase so
loosely that the connection to the original text is lost.

{_FORBIDDEN_ACTIONS}

Return ONLY a single JSON object with this exact shape (six triggers,
each an integer key; an evidence array). No prose, no markdown code
fences, no explanation outside the JSON:

{_SCHEMA_EXAMPLE}"""


def build_initial_prompt(marketing_copy: str) -> str:
    return f"""{_BASE_INSTRUCTIONS}

MARKETING COPY TO ANALYZE:
\"\"\"
{marketing_copy}
\"\"\"

Return the JSON object now."""


def build_repair_prompt(marketing_copy: str, validation_failure_reason: str) -> str:
    """Second and FINAL attempt. Gives Gemini the exact validation failure,
    not a vague "try again." Explicitly forbids inventing new evidence to
    patch the problem -- the fix must be a correction, not a workaround."""
    return f"""{_BASE_INSTRUCTIONS}

MARKETING COPY TO ANALYZE:
\"\"\"
{marketing_copy}
\"\"\"

Your previous response FAILED validation with this exact error:
{validation_failure_reason}

Return the complete JSON object again, correcting ONLY the identified
issue. Do not add new unsupported evidence to work around the error --
if you cannot support a nonzero score for a trigger with evidence that
genuinely appears in the copy, set that trigger's score to 0 instead.

Return the corrected JSON object now."""
