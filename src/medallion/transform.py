"""Deterministic, idempotent Silver and Gold transformations."""
from __future__ import annotations
from datetime import date
from pathlib import Path
from .io import read_jsonl, write_jsonl

def normalize_rate(raw: dict) -> dict:
    record_date = raw.get("record_date")
    # `is None` fallback (not `or`) so a legitimate 0 rate is not treated as missing.
    rate = next((raw[k] for k in ("avg_interest_rate_amt", "avg_interest_rate", "rate")
                 if raw.get(k) not in (None, "")), None)
    instrument = raw.get("security_desc") or raw.get("security_type_desc") or raw.get("instrument") or "unspecified"
    if not record_date or rate is None:
        raise ValueError("record_date and interest rate are required")
    date.fromisoformat(record_date[:10])
    value = float(str(rate).replace(",", ""))
    if value < 0:
        raise ValueError("interest rate cannot be negative")
    return {"record_date": record_date[:10], "instrument": str(instrument).strip(), "rate_pct": value}

def build_layers(bronze_path: Path, root: Path, max_invalid_rate: float = 0.05) -> dict:
    raw_rows = read_jsonl(bronze_path)
    valid, rejects = {}, []
    for row in raw_rows:
        try:
            clean = normalize_rate(row)
            # Deterministic business key makes reruns overwrite the same Silver record.
            valid[(clean["record_date"], clean["instrument"])] = clean
        except (ValueError, TypeError) as exc:
            rejects.append({"reason": str(exc), "record": row})
    invalid_rate = len(rejects) / max(1, len(raw_rows))
    # Persist rejects first so a failed gate can still be diagnosed.
    write_jsonl(root / "silver" / "treasury_rates" / "_rejected.jsonl", rejects)
    if not valid or invalid_rate > max_invalid_rate:
        raise ValueError(f"Silver quality gate failed: valid={len(valid)} invalid_rate={invalid_rate:.3f}")
    silver_rows = sorted(valid.values(), key=lambda r: (r["record_date"], r["instrument"]))
    silver = root / "silver" / "treasury_rates" / "data.jsonl"
    write_jsonl(silver, silver_rows)
    # Single pass; silver_rows is date-ordered so the last row per instrument is the latest.
    groups: dict[str, list[float]] = {}
    latest: dict[str, dict] = {}
    for row in silver_rows:
        groups.setdefault(row["instrument"], []).append(row["rate_pct"])
        latest[row["instrument"]] = row
    gold_rows = [{"instrument": name, "observations": len(values), "avg_rate_pct": round(sum(values)/len(values), 6),
                  "min_rate_pct": min(values), "max_rate_pct": max(values),
                  "latest_rate_pct": latest[name]["rate_pct"],
                  "as_of_date": latest[name]["record_date"]}
                 for name, values in sorted(groups.items())]
    gold = root / "gold" / "treasury_rate_summary" / "data.jsonl"
    write_jsonl(gold, gold_rows)
    return {"bronze_rows": len(raw_rows), "silver_rows": len(silver_rows), "rejected_rows": len(rejects),
            "gold_rows": len(gold_rows), "invalid_rate": invalid_rate, "silver_path": str(silver), "gold_path": str(gold)}
