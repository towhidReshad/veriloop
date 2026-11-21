"""Public VeriLoop pages must not include academic-only demonstrations or study dashboards."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_public_pages_are_product_workflows_only():
    page_names = {p.name for p in (ROOT / "pages").glob("*.py")}
    assert "5_Professor_Demo.py" not in page_names
    assert "4_Research_Dashboard.py" not in page_names
    homepage = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "Professor demo" not in homepage
    assert "pages/5_Professor_Demo.py" not in homepage
    assert "research dashboard" not in homepage.lower()

def test_study_dashboard_kept_separate_from_public_pages():
    research_page = ROOT / "research" / "research_dashboard_app.py"
    assert research_page.is_file()
    content = research_page.read_text(encoding="utf-8")
    assert "summarize_sample" in content
    assert "Observed counts" in content
