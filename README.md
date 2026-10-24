# KopiDate

Portfolio piece untuk role **AI Systems Engineering / Data Engineering**.

Repo ini mendemonstrasikan kemampuan: data engineering, SQL, Python, dashboarding, Google Apps Script, Claude Code workflow, dan operational reliability.

Data di repo ini **synthetic** — PT KopiXYZ Indonesia adalah perusahaan dummy.

---

## Gap yang diisi oleh repo ini

| Gap dari listing | Di-manifestasikan oleh |
|----------------|----------------------|
| SQL JOIN & agregasi | `pipeline/queries.sql` — 6 query dengan JOIN, window fn, aggregation |
| Data cleansing multi-source | `pipeline/pipeline.py` — 3 sumber (POS, Sheets, master) ke 1 warehouse |
| Data pipeline daily | `pipeline/pipeline.py` — end-to-end ETL dengan cleansing report |
| Dashboard performa akurat | `dashboard.py` — Streamlit dashboard, angka dari warehouse, ada filter |
| Google Apps Script + automasi | `apps_script/daily_ops_report.gs` — report harian otomatis ke email |
| Claude Code workflow | `docs/ai-verification-workflow.md` — proses review sebelum commit |
| Verifikasi output AI | `docs/ai-verification-workflow.md` — 3 contoh nyata |
| Operational reliability | `ops/runbook.md` + `ops/simulate_failure.py` — failure recovery drill |
| Dokumentasi proses | `docs/cleansing-decisions.md` + `docs/data-dictionary.md` |
| Git discipline | Branch → commit message convention → PR-ready structure |

---

## Struktur Repo

```
KopiDate/
├── README.md                    <- kamu ada di sini
├── requirements.txt
├── dashboard.py                 <- [PIECE 0] Operations Dashboard (Streamlit)
├── .streamlit/config.toml       theme config (dark default)
├── pipeline/                    <- [PIECE 1] POS Data Pipeline
│   ├── generate_sample_data.py  generate dirty POS data
│   ├── pipeline.py              ETL: extract -> transform -> load
│   ├── queries.sql              analytical SQL (JOIN, aggregation)
│   ├── run.sh                   one-liner end-to-end
│   └── README.md
├── apps_script/                 <- [PIECE 2] Google Apps Script
│   ├── daily_ops_report.gs      daily email report automation
│   └── README.md
├── docs/                        <- [PIECE 3] AI Workflow & Data Quality
│   ├── ai-verification-workflow.md  proses review AI-generated code
│   ├── cleansing-decisions.md   log cleansing decision + alasan
│   └── data-dictionary.md       dokumentasi schema warehouse
└── ops/                         <- [PIECE 4] Reliability Drill
    ├── runbook.md               failure matrix + recovery procedures
    └── simulate_failure.py       simulated failure scenarios
```

---

## Cara Menjalankan

```bash
# 1. Install
pip install -r requirements.txt

# 2. Generate data + run pipeline
python pipeline/generate_sample_data.py
python pipeline/pipeline.py

# 3. Run analytical queries
duckdb pipeline/KopiDate.duckdb < pipeline/queries.sql

# 4. Launch dashboard
streamlit run dashboard.py        # buka http://localhost:8501

# 5. Drill failure recovery
python ops/simulate_failure.py --scenario=all
```

---

## Dashboard

`dashboard.py` — Streamlit + Plotly, baca langsung dari DuckDB warehouse.

**Isi:**
- 8 KPI cards (revenue, orders, avg ticket, peak day, top menu/payment, ...)
- Daily revenue trend (line chart, dash + marker per outlet — bukan color saja)
- Revenue per outlet, top 5 menu, revenue by category (horizontal bar)
- Payment mix (donut), revenue by shift (grouped bar)
- Panel pipeline health: cleansing report + data quality
- Sidebar filter: outlet, menu, payment, date range

**Theme:** dark by default, mengikuti Streamlit theme toggle.
Semua warna pakai semantic token (`THEMES` dict di `dashboard.py`) — light dan dark dicek terpisah untuk kontras >= 4.5:1.

---

## Tech Stack

- **Python 3** + pandas (data processing)
- **DuckDB** (in-process analytical DB)
- **SQL** (JOIN, aggregation, window functions)
- **Streamlit + Plotly** (dashboard)
- **Google Apps Script / JavaScript** (automation)
- **Git** (version control, branch/PR workflow)

---

## Apa yang tidak ada di repo ini (dan mengapa)

- No cloud infrastructure (local demo, portable)
- No incremental/delta pipeline (full refresh untuk simplicity)
- No fuzzy matching untuk menu item (mapping eksplisit lebih reliable)
- No real-time streaming (batch processing daily)
- No auth/multi-user (single-user analytics tool)
- No cloud deployment (Apps Script deploy instructions ada di apps_script/)

Semua yang tidak ada masih relevan untuk production — lihat `ops/runbook.md` dan `docs/cleansing-decisions.md` untuk planning.

---

## Kontak

Portfolio project untuk keperluan lamaran kerja.
Silakan explore, run, dan modify sesuai kebutuhan.
