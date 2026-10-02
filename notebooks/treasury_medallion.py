# Databricks notebook source
# Azure-oriented Spark/Delta reference. Configure storage and credentials with
# secret scopes or Unity Catalog external locations; never hard-code access keys.
from pyspark.sql import functions as F

storage_root = dbutils.widgets.get("storage_root")  # abfss://lake@account.dfs.core.windows.net
source_url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?page%5Bsize%5D=1000&sort=-record_date"
payload = spark.read.option("multiline", "true").json(source_url)
bronze = (payload.select(F.explode("data").alias("r")).select("r.*")
          .withColumn("_ingested_at", F.current_timestamp())
          .withColumn("_source", F.lit("us_treasury_fiscaldata")))
bronze_path = f"{storage_root}/bronze/treasury_rates"
bronze.write.format("delta").mode("append").option("mergeSchema", "true").save(bronze_path)

raw = spark.read.format("delta").load(bronze_path)
silver = (raw.select(F.to_date("record_date").alias("record_date"),
                     F.coalesce("security_desc", "security_type_desc").alias("instrument"),
                     F.col("avg_interest_rate_amt").cast("double").alias("rate_pct"),
                     "_ingested_at", "_source")
          .filter(F.col("record_date").isNotNull() & F.col("instrument").isNotNull()
                  & F.col("rate_pct").isNotNull() & (F.col("rate_pct") >= 0))
          .dropDuplicates(["record_date", "instrument"]))
silver_path = f"{storage_root}/silver/treasury_rates"
silver.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(silver_path)

gold = (silver.groupBy("instrument").agg(
    F.count("*").alias("observations"), F.round(F.avg("rate_pct"), 6).alias("avg_rate_pct"),
    F.min("rate_pct").alias("min_rate_pct"), F.max("rate_pct").alias("max_rate_pct"),
    F.max_by("rate_pct", "record_date").alias("latest_rate_pct"),
    F.max("record_date").alias("as_of_date")))
gold_path = f"{storage_root}/gold/treasury_rate_summary"
gold.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(gold_path)
display(gold)
