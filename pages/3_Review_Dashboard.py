"""Password-gated, opt-in pilot reviewer workspace. Never publicly approve.

For research demonstration, not a production authentication service.
"""
import hmac
import os

import streamlit as st

from veriloop.db import connect_db, init_db, seed_evidence
from veriloop.archive import (
    ArchiveError, create_encrypted_backup, restore_encrypted_backup,
)
from veriloop.review import ReviewPolicyError, decide_review, linked_evidence, list_review_queue
from veriloop.corrections import (
    CorrectionPolicyError, default_draft, create_or_edit_draft,
    submit_for_approval, editorial_decision, markdown_export,
    record_export, list_corrections,
)

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
    # Prepared decrypted-in-memory session material is cleared on logout.
    # This does not delete files the owner already downloaded.
    st.session_state.pop("vl_encrypted_archive", None)
    st.session_state.pop("vl_backup_password", None)
    st.session_state.pop("vl_restore_password", None)
    st.rerun()

st.warning("Cloud SQLite is ephemeral. Do not use it as permanent approved-review storage; backup required. Do not approve unverifiable claims.")

with st.expander("Private encrypted backup / recovery · owner only"):
    st.info(
        "Free Streamlit Cloud does not preserve SQLite reliably across restarts. "
        "Download a password-encrypted archive after important review decisions; "
        "store it and its passphrase separately and privately. "
        "This does not provide automatic cloud backups."
    )
    with st.form("vl_make_encrypted_backup"):
        archive_passphrase = st.text_input(
            "New private archive passphrase (16+ characters)", type="password",
            key="vl_backup_password",
        )
        make_archive = st.form_submit_button("Prepare encrypted backup")
    if make_archive:
        try:
            with connect_db() as backup_conn:
                init_db(backup_conn)
                seed_evidence(backup_conn)
                encrypted = create_encrypted_backup(backup_conn, archive_passphrase)
            st.session_state["vl_encrypted_archive"] = encrypted
            st.success("Encrypted snapshot prepared. Download it and store your passphrase privately.")
        except (ArchiveError, OSError) as exc:
            st.error(f"Backup was not created: {exc}")
    archive_bytes = st.session_state.get("vl_encrypted_archive")
    if isinstance(archive_bytes, bytes):
        st.download_button(
            "Download encrypted .vlbackup file",
            archive_bytes,
            file_name="veriloop-private-review.vlbackup",
            mime="application/octet-stream",
            key="vl_download_private_archive",
        )
        if st.button("Clear prepared archive from this browser session"):
            st.session_state.pop("vl_encrypted_archive", None)
            st.rerun()
    st.divider()
    st.caption(
        "Restore is permitted only if this instance contains no user-created "
        "videos, review requests, or corrections. Existing data is never overwritten."
    )
    with st.form("vl_restore_private_archive"):
        private_file = st.file_uploader("Encrypted VeriLoop backup", type=["vlbackup"])
        restore_password = st.text_input(
            "Archive passphrase", type="password", key="vl_restore_password"
        )
        confirm_restore = st.checkbox(
            "I own this backup and understand it restores only into an empty research database"
        )
        restore_action = st.form_submit_button("Validate and restore private archive")
    if restore_action:
        if not confirm_restore or private_file is None:
            st.warning("Select an encrypted backup and confirm ownership before restoring.")
        elif private_file.size > 8 * 1024 * 1024 + 256:
            st.error("The encrypted backup exceeds the maximum permitted file size.")
        else:
            try:
                with connect_db() as restore_conn:
                    init_db(restore_conn)
                    seed_evidence(restore_conn)
                    restore_encrypted_backup(
                        restore_conn, private_file.getvalue(), restore_password
                    )
                st.session_state.pop("vl_encrypted_archive", None)
                st.success("Backup integrity validated and research records restored.")
                st.rerun()
            except (ArchiveError, OSError) as exc:
                st.error(f"Restore refused: {exc}")

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
else:

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


st.divider()
st.subheader("Editorial corrections · separate approval and export")
st.caption("A human claim review is NOT editorial permission. Corrections are manual Markdown files; nothing is posted.")
with connect_db() as conn:
    init_db(conn)
    approved = [r for r in list_review_queue(conn)
                if r["review_status"] == "APPROVED"
                and r["reviewed_verdict"] not in (None, "INSUFFICIENT_EVIDENCE")]
    corrections = list_corrections(conn)

if approved:
    chosen = st.selectbox(
        "Approved review for a correction",
        [r["review_id"] for r in approved],
        format_func=lambda rid: f"Review #{rid} · " + next(
            r["claim_text"][:90] for r in approved if r["review_id"] == rid
        ),
        key="correction_review",
    )
    with connect_db() as conn:
        init_db(conn)
        try:
            initial = default_draft(conn, chosen)
        except CorrectionPolicyError:
            initial = ""
    with st.form("correction_draft"):
        drafter = st.text_input("Draft editor identifier", max_chars=80)
        draft = st.text_area("Editable correction draft", value=initial, height=280)
        save = st.form_submit_button("Save correction draft")
    if save:
        try:
            with connect_db() as conn:
                init_db(conn)
                cid = create_or_edit_draft(conn, chosen, draft, editor_id=drafter)
            st.success(f"Draft #{cid} saved. NOT approved or exported.")
        except CorrectionPolicyError as exc:
            st.warning(str(exc))
else:
    st.info("No eligible human-approved claims. Review a specific evidence-linked claim first.")

if corrections:
    st.write("**Existing correction records**")
    cid = st.selectbox(
        "Select correction",
        [c["id"] for c in corrections],
        format_func=lambda ident: next(
            f"Correction #{c['id']} · {c['approval_status']}" for c in corrections if c["id"] == ident
        ),
        key="selected_correction",
    )
    selected = next(c for c in corrections if c["id"] == cid)
    st.write("Status:", selected["approval_status"])
    st.caption("Review reference: #" + str(selected["review_id"]))
    if selected["approval_status"] == "DRAFT":
        if st.button("Submit draft for independent editorial approval"):
            try:
                with connect_db() as conn:
                    init_db(conn)
                    submit_for_approval(conn, cid)
                st.success("Submitted for editorial approval. No export permitted yet.")
                st.rerun()
            except CorrectionPolicyError as exc:
                st.warning(str(exc))
    if selected["approval_status"] == "PENDING_APPROVAL":
        with st.form("editorial_approval"):
            editor = st.text_input("Editorial approver identifier", max_chars=80)
            rationale = st.text_area("Independent editorial rationale (25+ characters)")
            agree = st.checkbox("I independently checked the correction wording, reviewed claim and source")
            decision = st.radio("Editorial decision", ["REJECT", "APPROVE"], horizontal=True)
            submitted = st.form_submit_button("Record separate editorial decision")
        if submitted:
            if not agree:
                st.warning("Independent editorial confirmation is required.")
            else:
                try:
                    with connect_db() as conn:
                        init_db(conn)
                        editorial_decision(
                            conn, cid, approve=decision == "APPROVE",
                            editor_id=editor, rationale=rationale,
                        )
                    st.success("Editorial decision recorded separately from claim review.")
                    st.rerun()
                except CorrectionPolicyError as exc:
                    st.warning(str(exc))
    if selected["approval_status"] in ("APPROVED", "EXPORTED"):
        try:
            with connect_db() as conn:
                init_db(conn)
                filename, contents = markdown_export(conn, cid)
            st.download_button(
                "Download editorial-approved Markdown correction",
                data=contents.encode("utf-8"),
                file_name=filename,
                mime="text/markdown",
                key=f"approved_export_{cid}",
            )
            if st.button("Record that export was downloaded", key=f"record_export_{cid}"):
                with connect_db() as conn:
                    init_db(conn)
                    record_export(conn, cid)
                st.success("Export status recorded in temporary pilot database.")
                st.rerun()
        except CorrectionPolicyError as exc:
            st.warning(str(exc))
st.caption(
    "Free Streamlit Cloud database is ephemeral. Keep approved exports in a private archive. "
    "No public correction is posted automatically."
)
