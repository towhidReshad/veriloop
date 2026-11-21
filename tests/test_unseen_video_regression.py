"""Regression: a question followed by a program title is not a factual assertion."""
import pytest

from veriloop.claims import extract_claims

@pytest.mark.parametrize("headline", [
    "What do tech pioneers think about the AI revolution? - The Engineers, BBC World Service",
    "Can scientists accurately predict earthquakes? - News Explained",
    "Why does the sky change color? | Science Hour",
    "Are vaccines safe? - Expert Discussion",
    "How will AI change the world? | The Interview",
])
def test_question_with_program_suffix_is_not_claim(headline):
    assert extract_claims(headline, "") == []


def test_bbc_unseen_video_removes_question_and_keeps_declarative_metadata():
    title = "What do tech pioneers think about the AI revolution? - The Engineers, BBC World Service"
    description = (
        "Intelligent machines are remaking our world.\n"
        "The speed of their improvement is accelerating fast and every day there are more things they can do better than us.\n"
        "There are risks, but the opportunities for human society are enormous.\n"
        "David Silver is Principal Research Scientist at Google DeepMind."
    )
    found = extract_claims(title, description)
    assert all(x.source_field != "title" for x in found)
    assert any("David Silver" in x.text for x in found)


def test_assertive_headline_still_detected():
    result = extract_claims("A total solar eclipse crossed North America in 2024.", "")
    assert len(result) == 1 and result[0].source_field == "title"
