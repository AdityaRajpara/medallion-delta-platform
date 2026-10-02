from __future__ import annotations
import argparse
import json
import logging
from pathlib import Path
from .ingest import ingest
from .transform import build_layers

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local medallion pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--source", choices=("sample", "treasury"), default="sample")
    run.add_argument("--config", default="config/local.json")
    args = parser.parse_args()
    settings = json.loads(Path(args.config).read_text(encoding="utf-8"))
    logging.basicConfig(level=getattr(logging, settings.get("logging", {}).get("level", "INFO").upper()))
    root = Path(settings.get("data_root", "data"))
    bronze = ingest(args.source, root, settings)
    metrics = build_layers(bronze, root, settings.get("quality", {}).get("max_invalid_rate", 0.05))
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
