"""Password-gated, opt-in pilot reviewer workspace. Never publicly approve.

For research demonstration, not a production authentication service.
"""
import hmac
import os

import streamlit as st

from veriloop.db import connect_db, init_db, seed_evidence
from veriloop.review import ReviewPolicyError, decide_review, linked_evidence, list_review_queue

st.set_page_config(page_title="Reviewer Workspace | VeriLoop", page_icon="🔒")
st.title("Restricted human-review workspace")
st.caption("Review access is limited to an owner-configured password. No decision is automatic.")

try:
    password = st.secrets.get("REVIEWER_PASSWORD", os.getenv("REVIEWER_PASSWORD", ""))
except Exception:
    password = os.getenv("REVIEWER_PASSWORD", "")

if not isinstance(password, str) or len(password) < 16:
    st.warning("Reviewer dashboard is locked. Owner must privately configure REVIEWER_PASSWORD (16+ characters) in Streamlit Cloud Secrets. Never add it to GitHub.")
    st.stop()

if st.session_state.get("vl_review_authenticated") is not True:
    with st.form("reviewer_login"):
        attempt = st.text_input("Reviewer access password", type="password")
        login = st.form_submit_button("Unlock reviewer workspace")
    if login:
        count = int(st.session_state.get("vl_failed_logins", 0))
        if count >= 5:
            st.error("Too many attempts this session. Close this session and contact the project owner.")
        elif hmac.compare_digest(attempt, password):
            st.session_state["vl_review_authenticated"] = True
            st.session_state["vl_failed_logins"] = 0
            st.rerun()
        else:
            st.session_state["vl_failed_logins"] = count + 1
            st.error("Incorrect reviewer password")
    st.stop()

if st.button("Lock workspace", key="logout"):
    st.session_state["vl_review_authenticated"] = False
    st.rerun()

st.warning("Cloud SQLite is ephemeral. Do not use it as permanent approved-review storage; backup required. Do not approve unverifiable claims.")
try:
    with connect_db() as conn:
        init_db(conn)
        seed_evidence(conn)
        queue = list_review_queue(conn)
except Exception:
    st.error("Unable to load review queue. No decision was made.")
    st.stop()

st.write("**Requests currently stored in this session's database:**", len(queue))
if not queue:
    st.info("No requests have been submitted yet. Users can request a review from Verify News.")
    st.stop()

request_ids = {int(r["review_id"]): r for r in queue}
selected = st.selectbox("Select an individual claim request", list(request_ids),
                        format_func=lambda rid: f"#{rid} · {request_ids[rid]['review_status']} · {request_ids[rid]['claim_text'][:65]}")
request = request_ids[selected]
st.write("**Video:**", request["title"])
st.write("**Platform channel ID:**", request["youtube_channel_id"])
st.write("**Exact candidate claim:**", request["claim_text"])
st.write("**Tentative metadata stance:**", request["stance"])
st.caption("Claim context captured at submission: " + (request["claim_context"] or "not available"))
st.write("**Current reviewer status:**", request["review_status"])

with connect_db() as conn:
    matches = linked_evidence(conn, request["claim_id"])

if matches:
    for m in matches:
        st.write("Evidence", m["evidence_id"], "—", m["claim_text"])
        st.caption(f"Context: {m['context_status']} · Similarity {m['similarity_score']:.2f} (retrieval only)")
        st.link_button("Original evidence: " + m["source_name"], m["source_url"])
else:
    st.info("No local evidence was linked. APPROVED requires a matched, aligned source; use NEEDS_MORE_EVIDENCE instead.")

with st.form("reviewer_decision"):
    reviewer = st.text_input("Reviewer identifier (your actual name or team reviewer code)", max_chars=80)
    action = st.selectbox("Review decision", ["NEEDS_MORE_EVIDENCE", "REJECTED", "APPROVED"])
    verdict = st.selectbox("Claim-level verdict (used ONLY if APPROVED)",
                          ["SUPPORTED", "CONTRADICTED", "MISLEADING_CONTEXT", "INSUFFICIENT_EVIDENCE"])
    evidence_ids = [m["evidence_id"] for m in matches if m["context_status"] == "ALIGNED"]
    evidence_id = st.selectbox("Evidence for approval (requires ALIGNED context)",
                              ["-- none --"] + evidence_ids)
    note = st.text_area("Detailed decision rationale / revisions", max_chars=2000)
    checked = st.checkbox("I independently checked this exact claim, uploader stance, event, date, location and evidence; not just TF-IDF similarity")
    submit = st.form_submit_button("Save HUMAN review decision")

if submit:
    try:
        with connect_db() as conn:
            init_db(conn)
            seed_evidence(conn)
            decide_review(conn, selected, action, reviewer_id=reviewer, note=note,
                          verdict=verdict if action == "APPROVED" else None,
                          evidence_id=evidence_id if action == "APPROVED" and evidence_id != "-- none --" else None,
                          confirmed_context=checked if action == "APPROVED" else False)
    except ReviewPolicyError as exc:
        st.warning(f"Decision was not saved: {exc}")
    except Exception:
        st.error("Technical database error. Review decision was not saved.")
    else:
        st.success("A human decision was saved in this temporary SQLite pilot. History includes only appropriately approved, evidenced claims.")
        st.caption("Reload this page to view the updated status. Nothing was published externally.")
