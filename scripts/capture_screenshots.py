"""Render README screenshots from real pipeline output (dev tool, no extra pip deps).
Needs a Chromium-based browser (Chrome, Brave, Edge or chromium) on the machine.
Run from the repo root: python scripts/capture_screenshots.py"""
import html
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")
from medallion.ingest import ingest  # noqa: E402
from medallion.io import read_jsonl, write_jsonl  # noqa: E402
from medallion.transform import build_layers  # noqa: E402

OUT = Path("docs/images")
BROWSERS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome", "chromium", "chromium-browser",
]
CSS = """body{margin:0;padding:28px;background:#fff;color:#1f2328;font:14px -apple-system,Segoe UI,sans-serif}
h2{margin:0 0 14px;font-size:18px}h3{margin:22px 0 8px;font-size:14px;color:#57606a}
pre{background:#0d1117;color:#e6edf3;padding:16px 18px;border-radius:8px;font:13px/1.5 Menlo,monospace;margin:0;white-space:pre-wrap}
table{border-collapse:collapse;width:100%}th,td{border:1px solid #d0d7de;padding:6px 10px;text-align:left}
th{background:#f6f8fa}td.n{text-align:right;font-variant-numeric:tabular-nums}
.tag{display:inline-block;padding:2px 9px;border-radius:10px;font-size:12px;color:#fff}
.b{background:#b5651d}.s{background:#6e7781}.g{background:#bf8700}.x{background:#cf222e}"""


def table(rows, cols):
    head = "".join(f"<th>{c}</th>" for c in cols)
    body = "".join("<tr>" + "".join(
        f"<td class='{'n' if isinstance(r.get(c), (int, float)) else ''}'>{html.escape(str(r.get(c, '')))}</td>"
        for c in cols) + "</tr>" for r in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def page(title, body):
    return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body><h2>{title}</h2>{body}</body></html>"


def shoot(browser, doc, name, height):
    src = Path(tempfile.mkdtemp()) / f"{name}.html"
    src.write_text(doc, encoding="utf-8")
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", f"--window-size=1100,{height}",
                    f"--screenshot={(OUT / (name + '.png')).resolve()}", src.as_uri()],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    browser = next((b for b in BROWSERS if Path(b).exists() or shutil.which(b)), None)
    if not browser:
        sys.exit("No Chromium-based browser found")
    OUT.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp())
    settings = json.loads(Path("config/local.json").read_text())
    bronze = ingest("sample", work, settings)
    metrics = build_layers(bronze, work)
    metrics = {k: (v if not k.endswith("_path") else v.replace(str(work) + "/", "")) for k, v in metrics.items()}
    cli = "$ medallion run --source sample --config config/local.json\n" + json.dumps(metrics, indent=2)
    shoot(browser, page("Pipeline run (sample source)", f"<pre>{html.escape(cli)}</pre>"), "pipeline_run", 300)

    silver = read_jsonl(work / "silver/treasury_rates/data.jsonl")
    gold = read_jsonl(work / "gold/treasury_rate_summary/data.jsonl")
    raw = read_jsonl(bronze)
    layers = (
        "<h3><span class='tag b'>Bronze</span> raw rows + lineage columns</h3>"
        + table(raw[:4], ["record_date", "security_desc", "avg_interest_rate_amt", "_source", "_ingested_at"])
        + "<h3><span class='tag s'>Silver</span> typed, deduplicated, quality-gated</h3>"
        + table(silver[:4], ["record_date", "instrument", "rate_pct"])
        + "<h3><span class='tag g'>Gold</span> instrument summary</h3>"
        + table(gold, ["instrument", "observations", "avg_rate_pct", "min_rate_pct", "max_rate_pct",
                       "latest_rate_pct", "as_of_date"]))
    shoot(browser, page("Bronze → Silver → Gold", layers), "medallion_layers", 660)

    bad = work / "bad.jsonl"
    write_jsonl(bad, raw[:3] + [{"record_date": "not-a-date", "rate": "x"}, {"record_date": "2025-01-31", "rate": "-1"}])
    try:
        build_layers(bad, work / "gate")
        msg = "unexpected pass"
    except ValueError as exc:
        msg = f"ValueError: {exc}"
    rejects = read_jsonl(work / "gate/silver/treasury_rates/_rejected.jsonl")
    gate = (f"<span class='tag x'>Gate failed</span><pre style='margin:12px 0 0'>{html.escape(msg)}</pre>"
            "<h3>Quarantined rows (_rejected.jsonl)</h3>"
            + table([{"reason": r["reason"], "record": json.dumps(r["record"])} for r in rejects], ["reason", "record"]))
    shoot(browser, page("Quality gate (max_invalid_rate = 0.05)", gate), "quality_gate", 300)
    print("wrote", *sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
