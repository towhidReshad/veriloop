"""Regression guard for non-factual audience prompts seen in NASA live metadata."""
import pytest
from veriloop.claims import extract_claims

NASA_TITLE = "2024 Total Solar Eclipse: Through the Eyes of NASA (Official Broadcast)"
NASA_DESCRIPTION = (
    "Watch live with us as a total solar eclipse moves across North America on April 8, 2024, "
    "traveling through Mexico, across the United States from Texas to Maine, "
    "and out across Canada's Atlantic coast.\n"
    "A total solar eclipse occurs when the Moon passes between the Sun and the Earth, "
    "completely blocking the face of the Sun.\n"
    "The sky will darken as if it were dawn or dusk.\n"
    "Throughout the broadcast, send us your questions in the chat using #askNASA "
    "for a chance to have them answered live.\n"
    "WARNING: Except during the brief total phase of a total solar eclipse, "
    "it is not safe to look directly at the Sun without specialized eye protection."
)


def test_nasa_audience_prompt_is_not_a_factual_claim():
    candidates = extract_claims(NASA_TITLE, NASA_DESCRIPTION)
    assert len(candidates) == 4
    assert all("send us your questions" not in c.text.lower() for c in candidates)
    assert candidates[0].text.startswith("a total solar eclipse moves")
    assert any("eye protection" in c.text.lower() for c in candidates)


@pytest.mark.parametrize("prompt", [
    "Throughout the broadcast, send us your questions in the chat using #askNASA.",
    "During the show, submit your questions so we can discuss them.",
    "Post your comments so our team can respond.",
    "Let us know if your question has been answered.",
])
def test_social_prompts_are_not_extracted(prompt):
    assert extract_claims("Broadcast updates", prompt) == []


def test_real_claim_not_suppressed_by_audience_prompt_guard():
    candidates = extract_claims("", "The 2024 total solar eclipse crossed Mexico, the United States and Canada.")
    assert len(candidates) == 1
