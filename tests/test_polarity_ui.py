"""Regression: source verdicts and lexical polarity do not transfer to videos."""
from types import SimpleNamespace
from veriloop.matching import compare_context, has_polarity_conflict
from veriloop.presentation import friendly_explanation, has_conflicting_wording
from veriloop.factcheck import LiveLookup, run_live_fallback


def assessment(text, reference, matched=True):
    ref = SimpleNamespace(reference_claim=reference)
    return SimpleNamespace(
        matches=(ref,) if matched else (),
        candidate=SimpleNamespace(text=text, stance="ASSERTS"),
        preliminary_state="POSSIBLE_EVIDENCE_MATCH" if matched else "INSUFFICIENT_EVIDENCE",
    )


def test_vaccine_autism_negation_is_not_support():
    a = assessment(
        "Although scientific evidence suggests that vaccines do not cause autism.",
        "Childhood vaccines cause autism.",
    )
    assert has_polarity_conflict(a.candidate.text, a.matches[0].reference_claim)
    assert has_conflicting_wording(a) is True
    assert "not supporting evidence" in friendly_explanation(a)


def test_vaccine_autism_headline_conflict():
    a = assessment(
        'The Risk of Autism Is Not Increased by "Too Many Vaccines".',
        "Childhood vaccines cause autism.",
    )
    assert has_conflicting_wording(a)
    assert compare_context(a.candidate.text, a.matches[0].reference_claim)[0] == "UNCONFIRMED"


def test_conflicting_local_match_still_runs_live_search():
    a = assessment(
        "Vaccines do not cause autism.", "Childhood vaccines cause autism."
    )
    calls = []
    def fake_lookup(query, key):
        calls.append(query)
        return LiveLookup("NO_RESULTS")
    outcomes = run_live_fallback([a], "PRIVATE-KEY", lookup=fake_lookup)
    assert calls == ["Vaccines do not cause autism."]
    assert outcomes[0].status == "NO_RESULTS"


def test_aligned_local_match_still_skips_live_search():
    a = assessment(
        "Vaccines cause autism.", "Childhood vaccines cause autism."
    )
    def never_called(*_):
        raise AssertionError("Local same-polarity topic should bypass live fallback")
    assert run_live_fallback([a], "PRIVATE-KEY", lookup=never_called) == {}


def test_conflicting_local_match_without_key_reports_unavailable():
    a = assessment(
        "Vaccines do not cause autism.", "Childhood vaccines cause autism."
    )
    outcomes = run_live_fallback([a], None)
    assert outcomes[0].status == "UNAVAILABLE"


def test_related_wording_does_not_make_truth_verdict():
    a = assessment(
        "Vaccines do not cause autism.", "Childhood vaccines cause autism."
    )
    assert "verdict" in friendly_explanation(a)
    assert "not supporting evidence" in friendly_explanation(a)
