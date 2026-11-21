"""Static check: F-07 reviewed state uses Streamlit's supported link_button props."""
from pathlib import Path

def test_reviewed_source_link_uses_supported_streamlit_signature():
    page=(Path(__file__).resolve().parents[1]/"pages"/"1_Verify_News.py").read_text()
    anchor='st.link_button(\n                    "See the original evidence for this reviewed finding",'
    assert anchor in page
    assert 'key=f"previously_reviewed_' not in page
