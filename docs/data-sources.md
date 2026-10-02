# Public data sources

The runnable example uses the **US Treasury Fiscal Data API**, an official open API for average interest rates. The local sample CSV is a small deterministic fixture, not a live snapshot.

| Source | Format / use | Link |
|---|---|---|
| US Treasury Fiscal Data, Average Interest Rates | REST JSON; default pipeline source. Page the endpoint for bounded extracts. | [Dataset and API](https://fiscaldata.treasury.gov/datasets/average-interest-rates-treasury-securities/) |
| Data.gov | Federal open-data catalog; discover datasets and APIs for additional domains. | [Data.gov](https://data.gov/) |
| NYC Open Data | Socrata REST API and CSV; e.g. 311 requests for an operations dataset. | [NYC Open Data](https://opendata.cityofnewyork.us/) |
| Databricks sample datasets | Built-in sample tables/files for Spark and lakehouse exercises; availability depends on workspace/runtime. | [Databricks sample datasets](https://docs.databricks.com/en/discover/databricks-datasets.html) |
| US Census Bureau APIs | Official API for demographic and economic enrichment. | [Census API](https://www.census.gov/data/developers/data-sets.html) |

Respect source terms, published rate limits, attribution, and privacy rules. Do not commit API keys, downloaded bulk data, or personal data. Add adapters in `src/medallion/ingest.py` and preserve raw payload and attribution metadata in Bronze.
