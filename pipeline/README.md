# POS Data Pipeline

Mengisi gap: **SQL JOIN & agregasi**, **data cleansing multi-source**, **data pipeline**, **dokumentasi proses ETL**.

---

## Quick Start

```bash
# Install deps
pip install -r requirements.txt

# Generate data + run pipeline (sekali jalan)
python pipeline/generate_sample_data.py
python pipeline/pipeline.py

# Atau satu command:
bash pipeline/run.sh

# Run analytical queries
duckdb pipeline/KopiDate.duckdb < pipeline/queries.sql
```

---

## Arsitektur

```
data/raw/
  pos_orders_jan.csv   <- POS export Order #1 (format A)
  pos_orders_feb.csv   <- POS export Order #2 (format A)
  sheets_export.csv    <- Google Sheets manual entry (format B)
  master_menu.csv      <- master data menu (clean)

pipeline/
  generate_sample_data.py   generate dirty POS data
  pipeline.py               ETL: extract -> transform -> load
  queries.sql               6 analytical queries (JOIN, aggregation)
  KopiDate.duckdb               warehouse (output)
```

---

## Apa yang dibersihkan (dan mengapa)

Lihat `docs/cleansing-decisions.md` untuk log lengkap setiap decision.

Ringkasan:

| Problem | Handling |
|---------|----------|
| Typo payment ("gopay", "OFO", "debit") | Canonical mapping, case-insensitive |
| Whitespace tersembunyi (" Dago") | `strip()` sebelum validate |
| Format tanggal beda (4 format) | Parse + normalize ke `YYYY-MM-DD` |
| Duplicate order_id | Dedup, keep first |
| Price mismatch master menu | Recompute dari master × size multiplier |
| qty <= 0 (void) | Drop, masukkan review queue |
| Unknown outlet / payment / size | Drop dengan logging |

---

## Analytical Queries

1. Daily revenue by outlet (time series)
2. Revenue per category (JOIN orders + menu)
3. Payment mix (finance reconciliation)
4. Top 3 menu per outlet (window function)
5. Shift performance (JOIN orders + menu)
6. Data quality check (NULL / zero detection)

---

## Drill / Simulasi Failure

```bash
python ops/simulate_failure.py --scenario=all
```

Merusak data secara terkontrol, jalankan pipeline, lihat error + recovery step.
