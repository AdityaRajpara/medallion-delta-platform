# Benchmark protocol

No benchmark result is checked in or claimed by this repository. Use this protocol before describing scale or performance on a résumé.

1. Freeze a dataset snapshot and record its source, row count, date range, and checksum.
2. Generate scale variants deterministically, preserving a fixed seed and documenting the generator.
3. Record hardware/cluster SKU, worker count, runtime versions, configuration, storage type, and cold/warm cache state.
4. Measure ingest, Bronze-to-Silver, Silver-to-Gold, and representative Gold query times separately; repeat each run at least three times.
5. Record input/output rows, rejected rows, bytes/files read and written, elapsed time, and relevant executor metrics.
6. Compare the same workload and settings before claiming any optimization; publish raw results and calculation method.

Report the observed environment and numbers as a benchmark result. Do not convert a local synthetic result into a production throughput claim.
