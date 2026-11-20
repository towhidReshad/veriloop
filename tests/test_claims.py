"""F-03: deterministic extraction/abstention/stance guards."""
import pytest
from veriloop.claims import extract_claims, infer_stance

NASA_DESCRIPTION = (
    "Watch live with us as a total solar eclipse moves across North America on April 8, 2024, "
    "traveling through Mexico, across the United States from Texas to Maine, "
    "and out across Canada's Atlantic coast."
)

def test_nasa_actual_description_produces_exact_substring_claim():
    found = extract_claims("2024 Total Solar Eclipse: Through the Eyes of NASA (Official Broadcast)", NASA_DESCRIPTION)
    assert len(found) == 1
    assert found[0].text.startswith("a total solar eclipse moves across North America")
    assert found[0].text.endswith("Canada's Atlantic coast.")
    assert found[0].source_field == "description"
    assert found[0].stance == "ASSERTS"

def test_entertainment_movie_fixtures_do_not_invent_claims():
    assert extract_claims(
        "THE REAL TIGER 2 Hindi Dubbed Full Movie | Mahesh Babu",
        "Experience an uplifting story of love, family and self-discovery in The Real Tiger 2. "
        "Subscribe for new Hindi movies. Comment below."
    ) == []

@pytest.mark.parametrize("title", [
    "2024 Total Solar Eclipse: Through the Eyes of NASA",
    "Did NASA really see an eclipse?",
    "New report!",
    "Watch live: Earthquake coverage",
    "Trailer: The Real Tiger",
    "", "2024",
])
def test_nonpropositional_titles_abstain(title):
    assert extract_claims(title, "") == []

def test_no_fabricated_translation_for_non_english():
    assert extract_claims("বাংলাদেশে ভূমিকম্প হয়েছে", "করোনাভাইরাস সম্পর্কে একটি খবর।") == []
    assert extract_claims("한국에서 지진이 발생했습니다", "새로운 뉴스") == []

def test_claim_from_headline_detected():
    claims = extract_claims("Scientists can predict earthquakes in 2024.", "")
    assert len(claims) == 1
    assert claims[0].source_field == "title"

def test_deduplication():
    assert len(extract_claims("Vaccines cause autism.", "Vaccines cause autism.")) == 1

def test_out_of_scope_input_limit_applied():
    desc = "The earthquake struck Japan in 2011.\n" * 60
    assert len(extract_claims("", desc)) == 1

def test_rejects_invalid_max_claims():
    with pytest.raises(ValueError):
        extract_claims("","",max_claims=0)
    with pytest.raises(ValueError):
        extract_claims("","",max_claims=6)

def test_debunking_title_scopes_description_without_accusation():
    c = extract_claims("Fact check: a viral video is misleading.",
                       "The clip shows Karachi mayor Murtaza Wahab falling into Gujjar Nala during a 2024 boat inspection.")
    assert c
    assert all(item.stance == "DEBUNKS" for item in c)

def test_quoted_claim_not_auto_endorsed():
    c = extract_claims("", "An online post claims that childhood vaccines cause autism.")
    assert len(c) == 1
    assert c[0].stance == "QUOTES"

def test_sensational_cue_is_not_verdict():
    stance, note = infer_stance("Shock: A total solar eclipse crossed the United States in 2024.")
    assert stance == "ASSERTS"
    assert "unverified" in note.lower()
