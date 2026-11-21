"""Title-aware relevance selection, not truth scoring or invented claims."""
from veriloop.claims import extract_claims


def test_seeker_vaccine_topic_claims_priority_over_generic_description():
    title = "Vaccines Do NOT Cause Autism! What Does?"
    description = (
        "However, sometimes it can lead to some harmful misinformation.\n"
        "Over the past 50 years, numerous conspiracy theories have materialized around public health matters.\n"
        "The editor says medical misinformation is widespread.\n"
        "Research on this topic can be very interesting and informative.\n"
        "The programme has interviews with leading scientific experts.\n"
        "The risk of autism is not increased by too many vaccines.\n"
        "Scientific evidence suggests that vaccines do not cause autism.\n"
    )
    result = extract_claims(title, description)
    texts = [x.text for x in result]
    assert len(result) == 5
    assert texts.index("The risk of autism is not increased by too many vaccines.") < texts.index(
        "However, sometimes it can lead to some harmful misinformation.")
    assert texts.index("Scientific evidence suggests that vaccines do not cause autism.") < texts.index(
        "However, sometimes it can lead to some harmful misinformation.")
    assert all(x.source_field == "description" for x in result)
    assert all(x.stance != "VERIFIED" for x in result)


def test_late_relevant_claim_is_not_lost_at_first_five():
    title = "Solar eclipse across Mexico: official coverage"
    filler = "\n".join(f"People were talking about this year's developments in sector {i}." for i in range(9))
    description = filler + "\nA solar eclipse crossed Mexico on April 8, 2024."
    found = extract_claims(title, description)
    assert len(found) == 5
    assert found[0].text == "A solar eclipse crossed Mexico on April 8, 2024."


def test_no_title_context_keeps_stable_source_order():
    claims = extract_claims("", "The earthquake struck Japan in 2011.\nThe earthquake struck India in 2012.")
    assert [x.text for x in claims] == [
        "The earthquake struck Japan in 2011.", "The earthquake struck India in 2012."
    ]


def test_title_question_is_never_treated_as_a_fact():
    claims = extract_claims(
        "What do experts think about vaccines? - BBC World Service",
        "Vaccines do not cause autism."
    )
    assert all(x.source_field == "description" for x in claims)


def test_topic_ranking_preserves_exact_metadata_text():
    sentence = "Scientific evidence suggests that vaccines do not cause autism."
    claims = extract_claims(
        "Vaccines and autism", "The event was reported in 2024.\n" + sentence
    )
    assert claims[0].text == sentence


def test_max_claims_still_bounded_and_deterministic():
    desc = "\n".join(f"The virus spread in Canada during 202{i}." for i in range(6))
    a = extract_claims("The virus spread in Canada.", desc)
    b = extract_claims("The virus spread in Canada.", desc)
    assert a == b and len(a) <= 5
