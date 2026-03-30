# /home/mohith/Catchup-Mohith/backend/app/services/po_state_machine.py
from backend.app.core.exceptions import InvalidStateTransitionException

LEGAL_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["submitted", "cancelled"],
    "submitted": ["acknowledged", "cancelled"],
    "acknowledged": ["shipped"],
    "shipped": ["received"],
    "received": ["closed"],
    "closed": [],
    "cancelled": [],
}


def validate_transition(current: str, target: str) -> None:
    if current not in LEGAL_TRANSITIONS:
        raise InvalidStateTransitionException(
            details={
                "current_state": current,
                "target_state": target,
                "message": "Unknown current state",
            }
        )

    if target not in LEGAL_TRANSITIONS[current]:
        raise InvalidStateTransitionException(
            details={
                "current_state": current,
                "target_state": target,
                "allowed_transitions": LEGAL_TRANSITIONS[current],
            }
        )
