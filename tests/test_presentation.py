"""The simplified interface must never overstate a preliminary match."""
from types import SimpleNamespace
import pytest

from veriloop.presentation import friendly_status, friendly_explanation, summarize


def item(state, stance="ASSERTS"):
    return SimpleNamespace(preliminary_state=state, candidate=SimpleNamespace(stance=stance))


def test_summary_counts_retrieval_only():
    data = [item("POSSIBLE_EVIDENCE_MATCH"), item("INSUFFICIENT_EVIDENCE"), item("POSSIBLE_EVIDENCE_MATCH")]
    summary = summarize(data)
    assert (summary.candidates, summary.related, summary.unmatched) == (3, 2, 1)


def test_zero_claims_summary():
    assert summarize([]).candidates == 0


@pytest.mark.parametrize("state", [
    "POSSIBLE_EVIDENCE_MATCH", "INSUFFICIENT_EVIDENCE",
    "PREVIOUSLY_REVIEWED_CONTEXT_MATCH", "ERROR_RETRIEVING_DATA",
])
def test_friendly_status_has_no_truth_probability(state):
    result = friendly_status(state)
    assert result and "%" not in result and "fake" not in result.lower()


@pytest.mark.parametrize("stance", ["DEBUNKS", "QUOTES", "UNCLEAR"])
def test_quoted_or_debunked_claim_does_not_inherit_verdict(stance):
    msg = friendly_explanation(item("POSSIBLE_EVIDENCE_MATCH", stance))
    assert "cannot infer" in msg


def test_insufficient_does_not_call_false():
    assert "does not mean it is false" in friendly_explanation(item("INSUFFICIENT_EVIDENCE"))


def test_possible_match_not_final_verdict():
    msg = friendly_explanation(item("POSSIBLE_EVIDENCE_MATCH"))
    assert "before any conclusion" in msg


def test_error_is_not_an_evidence_judgment():
    assert "No factual assessment" in friendly_explanation(item("ERROR_RETRIEVING_DATA"))
