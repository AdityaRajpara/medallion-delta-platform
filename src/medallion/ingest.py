"""Open-data ingestion adapters."""
from __future__ import annotations
import csv
import json
import logging
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from .io import write_jsonl

LOG = logging.getLogger(__name__)

def fetch_treasury(url: str, page_size: int = 1000, timeout: int = 30) -> list[dict]:
    """Fetch a bounded page from the US Treasury Fiscal Data API."""
    query = urllib.parse.urlencode({"page[size]": page_size, "sort": "-record_date"})
    request = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": "medallion-demo/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    return payload.get("data", [])

def ingest(source: str, root: Path, settings: dict) -> Path:
    """Write a source snapshot as immutable, run-stamped JSONL Bronze input."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if source == "sample":
        sample_path = Path("data/sample/treasury_rates.csv")
        with sample_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    elif source == "treasury":
        cfg = settings["source"]
        rows = fetch_treasury(cfg["treasury_url"], cfg.get("treasury_page_size", 1000), cfg.get("timeout_seconds", 30))
    else:
        raise ValueError(f"Unsupported source {source!r}; choose sample or treasury")
    if not rows:
        raise RuntimeError(f"Source {source} returned no rows")
    target = root / "bronze" / "treasury_rates" / f"ingested_at={stamp}" / "part-00000.jsonl"
    count = write_jsonl(target, ({**row, "_source": source, "_ingested_at": stamp} for row in rows))
    LOG.info("bronze_ingest source=%s rows=%d path=%s", source, count, target)
    return target
