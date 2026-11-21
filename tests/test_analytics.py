"""Frozen F-11: source-backed observational sample with honest zero counts."""
from pathlib import Path
import pytest
from veriloop.analytics import load_sample, summarize_sample

def test_empty_observational_sample_no_invented_statistics():
    path=Path(__file__).resolve().parents[1]/"research"/"news_dataset.csv"
    records=load_sample(path)
    summary=summarize_sample(records)
    assert records==[]
    assert summary["sample_size"]==0
    assert summary["resolved_count"]==0
    assert summary["unresolved_count"]==0

def test_sample_grouping_keeps_unresolved_and_category_separate():
    rows=[
        dict(item_id="OBS1", claim_verdict="SUPPORTED",event_id="E1",presentation_label="neutral",source_country_if_supported="",
             published_at="2024-04-08"),
        dict(item_id="OBS2", claim_verdict="MISLEADING_CONTEXT",event_id="E1",presentation_label="sensational",source_country_if_supported="",
             published_at="2024-04-09"),
        dict(item_id="OBS3", claim_verdict="",event_id="",presentation_label="",source_country_if_supported="",
             published_at="")
    ]
    s=summarize_sample(rows)
    assert s["sample_size"]==3
    assert s["resolved_count"]==2
    assert s["unresolved_count"]==1
    assert s["countries"]["Not documented"]==3
    assert s["events"]["E1"]==2
    assert s["verdicts"]["UNRESOLVED"]==1

def test_missing_required_columns_rejected(tmp_path):
    csv=tmp_path/"bad.csv";csv.write_text("item_id,claim_verdict\\nA,SUPPORTED\\n",encoding="utf-8")
    with pytest.raises(ValueError):load_sample(csv)

def test_duplicate_observation_ids_rejected(tmp_path):
    from veriloop.analytics import EXPECTED
    csv=tmp_path/"duplicate.csv"
    csv.write_text(",".join(EXPECTED)+"\\n"+",".join(["ID1"]+[""]*(len(EXPECTED)-1))+"\\n"+",".join(["ID1"]+[""]*(len(EXPECTED)-1))+"\\n")
    with pytest.raises(ValueError): load_sample(csv)
