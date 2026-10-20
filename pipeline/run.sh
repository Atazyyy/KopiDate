#!/usr/bin/env bash
# End-to-end run: generate dirty data -> cleanse -> load -> query
# Usage: bash pipeline/run.sh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=============================================="
echo " 1/2  Generate sample dirty POS data"
echo "=============================================="
python pipeline/generate_sample_data.py

echo ""
echo "=============================================="
echo " 2/2  Run cleansing pipeline -> DuckDB"
echo "=============================================="
python pipeline/pipeline.py

echo ""
echo "Done. DB: pipeline/KopiDate.duckdb"
echo "Run queries:  duckdb pipeline/KopiDate.duckdb < pipeline/queries.sql"