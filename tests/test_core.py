"""
M1PI core tests: JSON schema validation and cost/token helpers.

Run: make test  or  uv run pytest tests/test_core.py -v
"""
import json
import pytest

# Import from project root; run tests from repo root
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from src.run_query import (
    validate_response_schema,
    _estimate_cost_usd,
    _load_system_prompt,
    _user_message,
)


def test_valid_response_schema():
    """Valid JSON with answer, confidence, actions passes."""
    data = {
        "answer": "Go to Settings to reset your password.",
        "confidence": 0.9,
        "actions": ["Send reset link", "Confirm email"],
    }
    validate_response_schema(data)


def test_valid_response_schema_confidence_boundaries():
    """Confidence 0 and 1 are valid."""
    for c in (0, 1, 0.5):
        validate_response_schema({
            "answer": "Ok",
            "confidence": c,
            "actions": [],
        })


def test_invalid_response_missing_keys():
    """Missing required key raises."""
    with pytest.raises(ValueError, match="missing key"):
        validate_response_schema({"answer": "Hi", "confidence": 0.8})


def test_invalid_response_confidence_out_of_range():
    """Confidence outside [0,1] raises."""
    with pytest.raises(ValueError, match="confidence"):
        validate_response_schema({
            "answer": "Hi",
            "confidence": 1.5,
            "actions": [],
        })


def test_invalid_response_actions_not_list():
    """Actions must be a list of strings."""
    with pytest.raises(ValueError, match="actions"):
        validate_response_schema({
            "answer": "Hi",
            "confidence": 0.8,
            "actions": "not a list",
        })


def test_estimate_cost_usd():
    """Token count maps to positive cost."""
    cost = _estimate_cost_usd(1000, 200)
    assert cost > 0
    assert isinstance(cost, float)
    # Rough: 1000 input + 200 output ~ 0.00015 + 0.00012
    assert 0.0001 < cost < 0.01


def test_load_system_prompt_has_instructions():
    """System prompt is loaded and contains schema (no user input)."""
    text = _load_system_prompt()
    assert "answer" in text and "confidence" in text and "actions" in text
    assert "{{QUESTION}}" not in text


def test_user_message_returns_trimmed_question():
    """User message is only the raw question, separate from system."""
    assert _user_message("  How do I refund?  ") == "How do I refund?"


def test_json_output_is_valid():
    """Example API-like JSON parses and validates."""
    raw = '{"answer": "Contact billing.", "confidence": 0.85, "actions": ["Open ticket"]}'
    data = json.loads(raw)
    validate_response_schema(data)
    assert data["answer"] == "Contact billing."
    assert data["confidence"] == 0.85
    assert data["actions"] == ["Open ticket"]
