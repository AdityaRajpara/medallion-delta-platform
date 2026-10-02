# Azure deployment notes

## Suggested topology

- **ADLS Gen2** stores Delta tables under `bronze/`, `silver/`, and `gold/` containers or prefixes.
- **Azure Databricks** runs the PySpark/Delta transformation job in `notebooks/treasury_medallion.py`.
- **Azure Data Factory** triggers the Databricks job, handles schedule/dependencies/retries, and routes failure alerts.
- **Azure Monitor / Log Analytics** receives job and platform diagnostics. Add structured metrics and alert rules for freshness, failures, and rejected rows.
- **GitHub Actions** validates repository changes; use a protected deployment environment and workload identity federation for deployment credentials if adding automated deploys.

## Before a real deployment

Set up Unity Catalog and an ADLS external location with least-privilege access. Use managed identity or secret scopes for any credentials. Parameterize storage paths per environment. Define a watermark and Delta `MERGE` key; keep Bronze append-only, quarantine invalid rows, and make Silver/Gold writes atomic. Add API pagination and rate-limit handling, source SLA expectations, retention policies, schema-change procedures, and operational alerts.

`azure/databricks_job.yml` is a configuration sketch. Validate it against your workspace and deploy process; it is not a complete Databricks Asset Bundle. The provided notebook's direct Spark JSON URL read is a concise demo. For resilient production ingestion, fetch paginated API responses through a controlled ingestion task, land raw response payloads in Bronze, then transform the landed files.
