"""
POS Data Pipeline untuk PT KopiDate Indonesia (demo).

Tujuan: mengubah data POS kotor dari 3 sumber
  - data/raw/pos_orders_jan.csv       (POS export Order #1)
  - data/raw/pos_orders_feb.csv       (POS export Order #2)
  - data/raw/sheets_export.csv        (Google Sheets manual entry)
menjadi satu DuckDB warehouse bersih yang siap pakai untuk dashboard.

Tahap:
  1. EXTRACT  — baca 3 CSV, gabungkan schema
  2. TRANSFORM — bersihkan (typo, format, missing, duplicate, mismatch)
  3. LOAD     — tulis ke DuckDB sebagai tabel fakta `orders`
  4. REPORT   — print ringkasan sebelum/sesudah cleansing

Cara jalan: python pipeline.py
Output: KopiDate.duckdb (di repo root / pipeline/)

Setiap cleansing decision ada alasan — lihat juga docs/cleansing-decisions.md.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DB_PATH = ROOT / "pipeline" / "KopiDate.duckdb"

# ── Master reference ─────────────────────────────────────────────────────────
OUTLET_CANONICAL = {"Dago", "Setiabudi", "Buah Batu"}
PAYMENT_CANONICAL = {
    "Cash", "QRIS", "GoPay", "OVO", "Dana", "ShopeePay", "Debit",
}
SIZE_CANONICAL = {"R", "L", "XL"}
SIZE_NORMALIZE = {
    "R": "R", "r": "R", "Reg": "R", "REGULAR": "R", "Reguler": "R", " reguler": "R",
    "L": "L", "l": "L", "Large": "L", "LARGE": "L", "besar": "L",
    "XL": "XL", "xl": "XL", "X-Large": "XL", "Extra Large": "XL",
}


# ── EXTRACT ──────────────────────────────────────────────────────────────────
def load_pos_files() -> pd.DataFrame:
    """Baca & union dua export POS, format konsisten."""
    df1 = pd.read_csv(RAW / "pos_orders_jan.csv")
    df2 = pd.read_csv(RAW / "pos_orders_feb.csv")
    pos = pd.concat([df1, df2], ignore_index=True)
    pos["__source"] = "pos"
    return pos


def load_sheets_export() -> pd.DataFrame:
    """Baca export Sheets yang format-nya beda, rename kolom ke standar POS."""
    df = pd.read_csv(RAW / "sheets_export.csv")
    rename = {
        "ID Pesanan": "order_id",
        "Tanggal": "order_date",
        "Outlet": "outlet",
        "Item": "menu_item",
        "Ukuran": "size",
        "Jumlah": "qty",
        "Harga Total": "price_idr",
        "Metode Bayar": "payment_method",
    }
    df = df.rename(columns=rename)
    df["shift"] = None         # Sheets tidak mencatat shift
    df["cashier"] = None       # Sheets tidak mencatat kasir
    df["__source"] = "sheets"
    keep = [
        "order_id", "order_date", "outlet", "menu_item", "size",
        "qty", "price_idr", "payment_method", "shift", "cashier", "__source",
    ]
    return df[keep]


# ── TRANSFORM ────────────────────────────────────────────────────────────────
def strip_string(s):
    if pd.isna(s):
        return s
    return re.sub(r"\s+", " ", str(s)).strip()


def normalize_outlet(s: str) -> str:
    if pd.isna(s):
        return None
    s = strip_string(s).title()  # "DAGO" / "dago" → "Dago"
    return s if s in OUTLET_CANONICAL else None


def normalize_payment(s: str) -> str:
    if pd.isna(s) or strip_string(s) == "":
        return None
    s = strip_string(s)
    # exact match (case-insensitive)
    for canon in PAYMENT_CANONICAL:
        if s.lower() == canon.lower():
            return canon
    return None  # unknown payment → drop & log


SIZE_MAP = {k.lower(): v for k, v in SIZE_NORMALIZE.items()}


def normalize_size(s):
    if pd.isna(s):
        return None
    raw = strip_string(s)
    return SIZE_MAP.get(raw.lower())


def parse_date(s):
    if pd.isna(s):
        return None
    raw = strip_string(s)
    fmts = ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%y", "%d %b %Y")
    for f in fmts:
        try:
            return datetime.strptime(raw, f).date()
        except ValueError:
            continue
    return None


def clean(df: pd.DataFrame, master_menu: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Pipeline utama: cleaning + validation. Mengembalikan (df_clean, stats)."""
    stats = {
        "input_rows": len(df),
        "dropped_missing_id": 0,
        "dropped_unknown_outlet": 0,
        "dropped_unknown_payment": 0,
        "dropped_unknown_size": 0,
        "dropped_unknown_menu": 0,
        "dropped_invalid_qty": 0,
        "dropped_duplicate": 0,
        "fixed_price_mismatch": 0,
        "filled_missing_shift": 0,
        "output_rows": 0,
    }

    # 1. Normalize strings
    for col in ["outlet", "menu_item", "payment_method", "size", "order_id"]:
        df[col] = df[col].apply(strip_string)

    # 2. Drop rows with missing critical id
    before = len(df)
    df = df[df["order_id"].notna() & (df["order_id"] != "")]
    stats["dropped_missing_id"] = before - len(df)

    # 3. Dedup exact duplicate rows (keep first)
    before = len(df)
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    stats["dropped_duplicate"] = before - len(df)

    # 4. Normalize outlet
    df["outlet"] = df["outlet"].apply(normalize_outlet)
    before = len(df)
    df = df[df["outlet"].notna()]
    stats["dropped_unknown_outlet"] = before - len(df)

    # 5. Normalize payment
    df["payment_method"] = df["payment_method"].apply(normalize_payment)
    before = len(df)
    df = df[df["payment_method"].notna()]
    stats["dropped_unknown_payment"] = before - len(df)

    # 6. Normalize size
    df["size"] = df["size"].apply(normalize_size)
    before = len(df)
    df = df[df["size"].notna()]
    stats["dropped_unknown_size"] = before - len(df)

    # 7. Normalize menu_item (whitespace + match to master)
    df["menu_item"] = df["menu_item"].apply(strip_string)
    valid_menu = set(master_menu["menu_item"])
    before = len(df)
    df = df[df["menu_item"].isin(valid_menu)]
    stats["dropped_unknown_menu"] = before - len(df)

    # 8. qty validation: drop negative & zero
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce")
    before = len(df)
    df = df[df["qty"].notna() & (df["qty"] > 0)]
    stats["dropped_invalid_qty"] = before - len(df)
    df["qty"] = df["qty"].astype(int)

    # 9. Parse date
    df["order_date"] = df["order_date"].apply(parse_date)
    df = df[df["order_date"].notna()]

    # 10. price_idr numeric
    df["price_idr"] = pd.to_numeric(df["price_idr"], errors="coerce").fillna(0).astype(int)

    # 11. Fix price mismatch: kalau price != master*size_multiplier, recompute
    def expected_price(row):
        for _, m in master_menu.iterrows():
            if m["menu_item"] == row["menu_item"]:
                mult = {"R": 1.0, "L": 1.3, "XL": 1.6}[row["size"]]
                return int(m["base_price_idr"] * mult)
        return None

    df["expected_price_idr"] = df.apply(expected_price, axis=1)
    mismatch = (df["price_idr"] != df["expected_price_idr"]) & df["expected_price_idr"].notna()
    stats["fixed_price_mismatch"] = int(mismatch.sum())
    df.loc[mismatch, "price_idr"] = df.loc[mismatch, "expected_price_idr"].astype(int)
    df = df.drop(columns=["expected_price_idr"])

    # 12. Shift: kalau missing, infer dari __source (POS = biarkan null)
    missing_shift = df["shift"].isna().sum()
    stats["filled_missing_shift"] = 0  # tidak auto-infer, biarkan null
    _ = missing_shift

    # 13. Revenue = qty * price
    df["revenue_idr"] = df["qty"] * df["price_idr"]

    stats["output_rows"] = len(df)

    return df.reset_index(drop=True), stats


# ── LOAD ─────────────────────────────────────────────────────────────────────
def load_to_duckdb(df: pd.DataFrame, master: pd.DataFrame) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE TABLE menu AS SELECT * FROM master")
    con.execute("CREATE TABLE orders AS SELECT * FROM df")
    con.close()


# ── REPORT ───────────────────────────────────────────────────────────────────
def report(stats: dict, con: duckdb.DuckDBPyConnection) -> None:
    print("\n" + "=" * 60)
    print("CLEANSING REPORT")
    print("=" * 60)
    for k, v in stats.items():
        print(f"  {k:<32} {v:>5}")

    print("\n" + "=" * 60)
    print("TOP 5 MENU BY REVENUE (Jan-Feb 2024)")
    print("=" * 60)
    res = con.execute("""
        SELECT menu_item, SUM(revenue_idr) AS revenue, SUM(qty) AS cups
        FROM orders
        GROUP BY menu_item
        ORDER BY revenue DESC
        LIMIT 5
    """).fetchdf()
    print(res.to_string(index=False))

    print("\n" + "=" * 60)
    print("REVENUE PER OUTLET PER SHIFT (sample — uses JOIN/aggregation)")
    print("=" * 60)
    res = con.execute("""
        SELECT outlet, shift,
               COUNT(*) AS n_orders,
               SUM(revenue_idr) AS revenue_idr
        FROM orders
        WHERE shift IS NOT NULL
        GROUP BY outlet, shift
        ORDER BY outlet, shift
    """).fetchdf()
    print(res.to_string(index=False))
    print()


def main() -> None:
    print(">> Loading sources...")
    pos = load_pos_files()
    sheets = load_sheets_export()
    raw = pd.concat([pos, sheets], ignore_index=True)
    print(f"   pos_orders rows: {len(pos)}")
    print(f"   sheets_export rows: {len(sheets)}")
    print(f"   combined raw rows: {len(raw)}")

    master = pd.read_csv(RAW / "master_menu.csv")
    print("\n>> Cleaning...")
    clean_df, stats = clean(raw, master)
    print(f"   output rows: {len(clean_df)}")

    print("\n>> Loading into DuckDB...")
    load_to_duckdb(clean_df, master)

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        report(stats, con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
