import pytest
from medallion.transform import build_layers, normalize_rate
from medallion.io import write_jsonl

def test_normalize_and_deduplicate(tmp_path):
    bronze = tmp_path / "bronze.jsonl"
    write_jsonl(bronze, [
        {"record_date":"2025-01-31", "security_desc":"Bills", "avg_interest_rate_amt":"4.2"},
        {"record_date":"2025-01-31", "security_desc":"Bills", "avg_interest_rate_amt":"4.2"},
    ])
    result = build_layers(bronze, tmp_path)
    assert result["bronze_rows"] == 2
    assert result["silver_rows"] == 1
    assert result["gold_rows"] == 1

def test_quality_gate_rejects_malformed_rows(tmp_path):
    bronze = tmp_path / "bronze.jsonl"
    write_jsonl(bronze, [{"record_date":"not-a-date", "rate":"x"}])
    with pytest.raises(ValueError, match="quality gate failed"):
        build_layers(bronze, tmp_path)

def test_negative_rate_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        normalize_rate({"record_date":"2025-01-01", "rate":"-0.1"})
