import re

from core.io_contract import StructuredResponse

# Deliberately deterministic (regex), not a second LLM call: a safety gate
# should behave the same way every time it sees the same text, not be
# subject to model sampling variance.
_ACTION_VERBS = (
    r"placed|cancell?ed|sent|submitted|issued|updated|modified|approved|"
    r"deleted|removed|created|processed|executed|confirmed|reordered|adjusted"
)

_FIRST_PERSON_CLAIM = re.compile(rf"\b(?:I|we)(?:'ve|\s+have)\s+(?:{_ACTION_VERBS})\b", re.IGNORECASE)
_PASSIVE_CLAIM = re.compile(rf"\b(?:has|have)\s+been\s+(?:{_ACTION_VERBS})\b", re.IGNORECASE)

_NEUTRALIZED_MARKER = "[PROPOSED -- NOT EXECUTED]"

_ADVISORY_LIMITATION = "This response is advisory only -- no action has been taken on your behalf."
_ADVISORY_NEXT_STEP = "Get human review and approval before executing any recommended action."

_VIOLATION_LIMITATION = (
    "The draft answer claimed an executed action; this has been neutralized -- "
    "no action was actually taken. Treat the neutralized text as a proposal only."
)


def _contains_action_claim(text: str) -> bool:
    return bool(_FIRST_PERSON_CLAIM.search(text) or _PASSIVE_CLAIM.search(text))


def _neutralize(text: str) -> str:
    text = _FIRST_PERSON_CLAIM.sub(_NEUTRALIZED_MARKER, text)
    text = _PASSIVE_CLAIM.sub(_NEUTRALIZED_MARKER, text)
    return text


def enforce_suggest_only(response: StructuredResponse) -> StructuredResponse:
    # Decision #10: the agent proposes, never executes. Inspect the FINAL
    # answer text (not the intermediate pipeline context) and neutralize any
    # claim of an already-executed action, then make the advisory nature
    # explicit on every response -- not only the ones that trip the check.
    if _contains_action_claim(response.answer):
        response.answer = _neutralize(response.answer)
        response.limitations = [*response.limitations, _VIOLATION_LIMITATION]

    response.limitations = [*response.limitations, _ADVISORY_LIMITATION]
    response.next_steps = [*response.next_steps, _ADVISORY_NEXT_STEP]
    return response
