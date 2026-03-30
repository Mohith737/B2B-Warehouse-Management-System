# /home/mohith/Catchup-Mohith/backend/tests/unit/test_po_state_machine.py
import pytest

from backend.app.core.exceptions import InvalidStateTransitionException
from backend.app.services.po_state_machine import validate_transition


def test_draft_to_submitted_is_legal():
    validate_transition("draft", "submitted")


def test_draft_to_cancelled_is_legal():
    validate_transition("draft", "cancelled")


def test_submitted_to_acknowledged_is_legal():
    validate_transition("submitted", "acknowledged")


def test_submitted_to_cancelled_is_legal():
    validate_transition("submitted", "cancelled")


def test_acknowledged_to_shipped_is_legal():
    validate_transition("acknowledged", "shipped")


def test_shipped_to_received_is_legal():
    validate_transition("shipped", "received")


def test_received_to_closed_is_legal():
    validate_transition("received", "closed")


def test_draft_to_acknowledged_is_illegal():
    with pytest.raises(InvalidStateTransitionException):
        validate_transition("draft", "acknowledged")


def test_draft_to_shipped_is_illegal():
    with pytest.raises(InvalidStateTransitionException):
        validate_transition("draft", "shipped")


def test_acknowledged_to_cancelled_is_illegal():
    with pytest.raises(InvalidStateTransitionException):
        validate_transition("acknowledged", "cancelled")


def test_shipped_to_cancelled_is_illegal():
    with pytest.raises(InvalidStateTransitionException):
        validate_transition("shipped", "cancelled")


def test_closed_to_any_is_illegal():
    with pytest.raises(InvalidStateTransitionException):
        validate_transition("closed", "received")


def test_cancelled_to_any_is_illegal():
    with pytest.raises(InvalidStateTransitionException):
        validate_transition("cancelled", "draft")
