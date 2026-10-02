# Cloud-Native Delta Lake Platform — Medallion Architecture

A portfolio-ready, local-first data engineering project that demonstrates **Bronze → Silver → Gold** processing with public data. The local pipeline runs on Python alone; optional paths show how the same domain maps to PySpark, Delta Lake, Azure Databricks, ADLS Gen2, Azure Data Factory, and Airflow.

> This repository is a project implementation and deployment blueprint. It does not claim production deployment, enterprise-scale throughput, 50M records per day, or measured latency/error reductions. Run the included benchmark before publishing any performance result.

## What it does

- Ingests a bounded page from the official US Treasury Fiscal Data REST API or a deterministic checked-in CSV fixture.
- Writes run-stamped, source-tagged raw JSONL to Bronze.
- Validates, types, and deduplicates to Silver using `(record_date, instrument)` as a business key; rejected rows are quarantined and a quality threshold gates publication.
- Aggregates Gold interest-rate summaries by instrument.
- Includes an optional Databricks Delta notebook, Airflow DAG example, Dockerfile, GitHub Actions CI, and deployment guidance.

## Quick start (local, no cloud account)

Requires Python 3.10 or newer.

```bash
cd medallion-delta-platform
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e '.[dev]'
medallion run --source sample --config config/local.json
```

The sample path needs no network. To pull a live public API page:

```bash
medallion run --source treasury --config config/local.json
```

Output paths are `data/bronze/treasury_rates/`, `data/silver/treasury_rates/`, and `data/gold/treasury_rate_summary/`. Local generated data is git-ignored. Running repeatedly is safe for the canonical Silver and Gold outputs; Bronze keeps each ingest run as a replayable snapshot.

### Docker

```bash
docker build -t medallion-delta-platform .
docker run --rm -v "$PWD/data:/app/data" medallion-delta-platform
```

### Optional Spark/Delta dependencies

```bash
python -m pip install -e '.[spark]'
```

The Spark notebook is designed for a Databricks workspace and ADLS Gen2 configuration; installing these libraries locally does not provision a Spark cluster or Azure resources.

## Architecture

See [architecture and lineage](docs/architecture.md) for the Mermaid diagram and table contracts. The main flow is:

```text
US Treasury REST API / CSV adapters → Bronze raw snapshots → Silver quality-gated canonical rates → Gold instrument summaries
```

### Example data model

| Layer | Dataset | Key fields |
|---|---|---|
| Bronze | `treasury_rates` | Raw source fields, `_source`, `_ingested_at` |
| Silver | `treasury_rates` | `record_date`, `instrument`, `rate_pct` |
| Gold | `treasury_rate_summary` | `instrument`, `observations`, `avg_rate_pct`, `min_rate_pct`, `max_rate_pct`, `latest_rate_pct`, `as_of_date` |

Machine-readable Silver and Gold contracts are in `schemas/`.

## Public data choices

The default public source is the US Treasury's [Average Interest Rates API](https://fiscaldata.treasury.gov/datasets/average-interest-rates-treasury-securities/). The [sample CSV](data/sample/treasury_rates.csv) is a tiny deterministic fixture for demos and CI, not a downloaded Treasury extract. More ideas and official links are in [docs/data-sources.md](docs/data-sources.md): Data.gov discovery, NYC Open Data REST/CSV, Databricks sample datasets, and US Census APIs.

The adapter currently implements Treasury API ingestion plus CSV fixture ingestion. Extend it with a downloader or source-specific REST adapter for additional CSV, JSON, or Parquet sources. Record source attribution and terms; do not commit credentials or personal data.

## Quality, logging, and operating signals

The lightweight quality gate requires valid dates, a parseable non-negative rate, at least one valid record, and an invalid-row percentage below `quality.max_invalid_rate` in `config/local.json`. Rejected records are kept in Silver's `_rejected.jsonl`. Standard Python logging records source, row count, and output path; the CLI emits row-count metrics. Add Azure Monitor/Datadog exporters at the orchestration boundary when deploying.

The repo provides a **single example Airflow DAG** for scheduled execution. It is not a production-scale 30-DAG deployment. For Azure, ADF can trigger a Databricks job and provide managed scheduling/retries; see [Azure deployment](docs/azure-deployment.md). GitHub Actions runs the automated test suite on pushes and pull requests.

## Azure Databricks and ADLS Gen2 deployment outline

1. Create or select an Azure Databricks workspace and an ADLS Gen2 storage account/container.
2. Grant the workspace identity access through Unity Catalog external locations (recommended) or a scoped secret-backed service principal. Never put storage keys in notebooks or Git.
3. Upload/deploy `notebooks/treasury_medallion.py`, configure its `storage_root` widget to an `abfss://` path, and adapt the job cluster settings in `azure/databricks_job.yml` to an approved runtime and cluster policy.
4. Create a Databricks job from the reference config. For orchestration, create an ADF pipeline with a Databricks notebook/job activity, retry policy, schedule or event trigger, and failure notifications.
5. Parameterize environment paths and add storage lifecycle, catalog permissions, monitoring, and alerting before using real workloads.

The notebook is a learning reference, not a turnkey deployment artifact: adapt API pagination, secret handling, schema evolution, quarantine behavior, watermarks, `MERGE` semantics, and workspace bundle settings for the target environment. Azure resources may incur charges.

## Repository map

```text
src/medallion/       dependency-free local ingest and transforms
notebooks/           Spark + Delta reference for Databricks
schemas/             Silver and Gold contracts
airflow/dags/        optional Airflow schedule example
azure/               Databricks job configuration reference
tests/                unit and pipeline quality tests
docs/                 architecture, sources, Azure deployment
config/               local source and quality settings
```

## GitHub: publish this project

This folder is already a local Git repository with an initial commit on `main`. Create a **new empty repository** on your GitHub account (do not initialize it with a README or license), then from this directory set the remote and push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Replace the URL with the repository you created. GitHub will run the CI workflow after the push. If you want this project created in an existing repository, first choose the repository and whether it should live at the root or in a subdirectory.

## Portfolio metrics

The implementation exposes counts and quality rate so you can report evidence after a real run. To make a credible scale claim, create a fixed synthetic/public-data benchmark, document machine and runtime settings, run it, and commit the measured output. See [benchmark protocol](docs/benchmarking.md). Do not reuse metrics from the original project description without measurement.
