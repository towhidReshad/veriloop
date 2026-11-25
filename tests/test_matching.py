"""F-04/F-05: local matching, abstention, event consistency and provenance."""
import pytest

from veriloop.claims import CandidateClaim
from veriloop.db import load_evidence, connect_db, init_db, list_evidence, seed_evidence
from veriloop.matching import assess_metadata, compare_context, retrieve_matches

REFERENCES = load_evidence()

def claim(text, stance="ASSERTS"):
    return CandidateClaim(text, "description", stance, "Metadata-only stance hypothesis")

def test_nasa_demo_finds_eclipse_reference_tentatively():
    analyses = assess_metadata("2024 Total Solar Eclipse: Through the Eyes of NASA (Official Broadcast)",
        "Watch live with us as a total solar eclipse moves across North America on April 8, 2024, "
        "traveling through Mexico, across the United States from Texas to Maine, and out across Canada's Atlantic coast.", REFERENCES)
    assert analyses
    assert analyses[0].preliminary_state == "POSSIBLE_EVIDENCE_MATCH"
    assert analyses[0].matches[0].evidence_id == "EV-002"
    assert analyses[0].matches[0].source_url.startswith("https://science.nasa.gov/")
    assert analyses[0].matches[0].context_status == "ALIGNED"
    assert "Tentative" in analyses[0].explanation

def test_movie_no_claim_no_verdict():
    assert assess_metadata("THE REAL TIGER 2 Hindi Dubbed Full Movie | Mahesh Babu",
        "Experience an uplifting story of love, family and self-discovery in The Real Tiger 2.", REFERENCES) == []

def test_misleading_karachi_example_stays_candidate_not_final_verdict():
    analyses = assess_metadata("Viral clip in Karachi",
        "The clip shows Karachi mayor Murtaza Wahab falling into Gujjar Nala during a 2024 boat inspection.",REFERENCES)
    assert analyses[0].preliminary_state == "POSSIBLE_EVIDENCE_MATCH"
    assert analyses[0].matches[0].evidence_id == "EV-001"
    assert analyses[0].matches[0].external_reference_classification == "MISLEADING_CONTEXT"
    assert "misleading verdict" not in analyses[0].preliminary_state.lower()

def test_fact_check_can_match_without_accusing_debunking_video():
    analyses = assess_metadata("Fact check: Karachi mayor story is a misleading claim",
        "The clip shows Karachi mayor Murtaza Wahab falling into Gujjar Nala during a 2024 boat inspection.", REFERENCES)
    assert analyses
    a = next(x for x in analyses if x.matches)
    assert a.candidate.stance == "DEBUNKS"
    assert a.matches[0].evidence_id == "EV-001"
    assert "No misleading label" in a.explanation

def test_quote_can_match_without_accusing():
    analyses = assess_metadata("Claims by an online post",
        "An online post claims that childhood vaccines cause autism.", REFERENCES)
    assert analyses[0].candidate.stance == "QUOTES"
    assert analyses[0].preliminary_state == "POSSIBLE_EVIDENCE_MATCH"
    assert "uploader stance" in analyses[0].explanation

def test_explicit_year_conflict_excludes_2024_reference():
    candidate = claim("A total solar eclipse crossed Mexico, the United States and Canada in 2026.")
    assert "EV-002" not in [m.evidence_id for m in retrieve_matches(candidate,REFERENCES)]
    assert compare_context(candidate.text,REFERENCES[1]["claim_text"])[0] == "INCOMPATIBLE"

def test_explicit_region_conflict_excludes_karachi_reference():
    candidate = claim("The clip shows Panaji mayor falling into water in India during a 2024 boat inspection.")
    assert "EV-001" not in [m.evidence_id for m in retrieve_matches(candidate, REFERENCES)]
    assert compare_context(candidate.text,REFERENCES[0]["claim_text"])[0] == "INCOMPATIBLE"

def test_polarity_difference_never_transfers_reference_verdict():
    state, note = compare_context("Childhood vaccines do not cause autism.", "Childhood vaccines cause autism.")
    assert state == "UNCONFIRMED"
    assert "polarity" in note.lower()

def test_no_match_means_insufficient_not_false():
    analyses = assess_metadata("A bird flew into my window.", "", REFERENCES)
    assert len(analyses) == 1
    assert analyses[0].preliminary_state == "INSUFFICIENT_EVIDENCE"
    assert not analyses[0].matches
    assert "does not mean" in analyses[0].explanation

def test_empty_evidence_does_not_create_fake_match():
    assert not retrieve_matches(claim("A total solar eclipse crossed Mexico, the United States and Canada in 2024."), [])

def test_sqlite_rows_supported_without_mutation(tmp_path):
    with connect_db(tmp_path / 'pilot.db') as conn:
        init_db(conn)
        seed_evidence(conn)
        rows = list_evidence(conn)
        matches = retrieve_matches(claim("A total solar eclipse crossed Mexico, the United States and Canada on April 8, 2024."), rows)
        assert matches and matches[0].evidence_id == "EV-002"
        assert conn.execute('SELECT COUNT(*) FROM assessments').fetchone()[0] == 0
        assert conn.execute('SELECT COUNT(*) FROM reviews').fetchone()[0] == 0

@pytest.mark.parametrize("top_k,threshold", [(0,0.2),(2,-0.3),(-1,0.2),(2,3)])
def test_invalid_retrieval_options(top_k,threshold):
    with pytest.raises(ValueError):
        retrieve_matches(claim("A total solar eclipse crossed in 2024."),REFERENCES, top_k=top_k,minimum_similarity=threshold)

def test_reference_order_stability():
    c = claim("A total solar eclipse crossed Mexico, United States and Canada on April 8, 2024.")
    ids_a = [m.evidence_id for m in retrieve_matches(c,REFERENCES)]
    ids_b = [m.evidence_id for m in retrieve_matches(c,list(reversed(REFERENCES)))]
    assert ids_a == ids_b

def test_multiple_years_and_locations_abstain():
    a,b = compare_context("A 2016 clip was mislabeled as a Karachi 2024 incident.", "The clip shows Karachi mayor falling in 2024.")
    assert a == "UNCONFIRMED"
    a,b = compare_context("The video mentions Karachi and India.", "The clip shows an incident in Karachi.")
    assert a == "UNCONFIRMED"


def test_live_karachi_video_spelling_variation_finds_afp_as_unconfirmed_lead():
    # Real YouTube description observed in owner browser, November 2026.
    # 'Naala' versus curated source 'Nala' and different wording previously
    # fell below the strict word TF-IDF retrieval threshold (0/1 matches).
    candidate = claim(
        "A funny but dangerous incident occurred when self proclaimed non "
        "constitutional and rigged mayor Karachi Barrister Murtaza Wahab "
        "had to taste their own medicine during a survey of Gujjar Naala."
    )
    results = retrieve_matches(candidate, REFERENCES)
    assert results
    assert results[0].evidence_id == "EV-001"
    assert results[0].source_name == "AFP Fact Check"
    assert results[0].context_status == "UNCONFIRMED"
    assert "spelling/wording lead" in results[0].context_note


def test_fuzzy_fallback_rejects_nonidentical_named_event():
    candidate = claim(
        "A funny but dangerous incident occurred during a survey in Karachi "
        "when a different mayor slipped near Gujjar Naala."
    )
    ids = [m.evidence_id for m in retrieve_matches(candidate, REFERENCES)]
    assert "EV-001" not in ids


def test_overlapping_capitalized_name_anchor():
    # A greedy non-overlapping two-word regex used to consume
    # "Barrister Murtaza" and miss "Murtaza Wahab" in live metadata.
    from veriloop.matching import _shared_named_anchor
    assert _shared_named_anchor(
        "Mayor Karachi Barrister Murtaza Wahab fell near Gujjar Naala.",
        "The clip shows Karachi mayor Murtaza Wahab falling into Gujjar Nala."
    )
    assert not _shared_named_anchor(
        "Mayor Karachi Barrister Someone Else fell near Gujjar Naala.",
        "The clip shows Karachi mayor Murtaza Wahab falling into Gujjar Nala."
    )
