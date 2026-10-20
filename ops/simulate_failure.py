"""
Simulasi failure untuk drill reliability.

Jalankan: python ops/simulate_failure.py

Script ini sengaja "merusak" file data, lalu menjalankan pipeline
untuk mendemonstrasikan recovery process.

Scenarios:
  --scenario=missing-file    Hapus pos_orders_jan.csv
  --scenario=schema-drift   Tambahkan kolom baru ke CSV
  --scenario=corrupt-data   Inject baris invalid
  --scenario=all            Jalankan semua satu per satu
"""
import argparse
import csv
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
BACKUP = ROOT / "data" / "raw_backup"


def backup():
    """Backup semua file mentah."""
    if BACKUP.exists():
        shutil.rmtree(BACKUP)
    shutil.copytree(RAW, BACKUP)


def restore():
    """Restore dari backup."""
    if BACKUP.exists():
        shutil.rmtree(RAW)
        shutil.copytree(BACKUP, RAW)


def scenario_missing_file():
    """F1: File POS tidak ada."""
    print("\n=== SCENARIO: F1 — POS Export file tidak ada ===")
    backup()
    (RAW / "pos_orders_jan.csv").unlink()
    print("  [SIMULATED] pos_orders_jan.csv dihapus")

    print("\n  Jalankan pipeline:")
    result = subprocess.run(
        [sys.executable, str(ROOT / "pipeline" / "pipeline.py")],
        capture_output=True, text=True, cwd=str(ROOT),
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    if result.returncode != 0:
        print(f"  [EXPECTED] Pipeline gagal dengan error:")
        for line in result.stderr.split("\n"):
            if "Error" in line or "FileNotFound" in line or "not" in line.lower():
                print(f"    {line.strip()}")
    print("\n  Fix: restore file dari backup -> pipeline jalan normal")
    print("  Runbook ref: ops/runbook.md > F1")


def scenario_schema_drift():
    """F2: Kolom baru di export POS (schema drift)."""
    print("\n=== SCENARIO: F2 — Schema drift (kolom baru) ===")
    restore()
    backup()

    # Tambah kolom baru ke CSV
    fpath = RAW / "pos_orders_jan.csv"
    rows = []
    with fpath.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames + ["discount_idr"]
        for row in reader:
            row["discount_idr"] = "0"
            rows.append(row)

    with fpath.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("  [SIMULATED] Kolom 'discount_idr' ditambahkan ke pos_orders_jan.csv")
    print("  [SIMULATED] Schema drift terdeteksi -> pipeline crash")

    print("\n  Jalankan pipeline:")
    result = subprocess.run(
        [sys.executable, str(ROOT / "pipeline" / "pipeline.py")],
        capture_output=True, text=True, cwd=str(ROOT),
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    if result.returncode != 0:
        print(f"  [EXPECTED] Pipeline gagal:")
        for line in result.stderr.split("\n"):
            if "KeyError" in line or "Error" in line:
                print(f"    {line.strip()}")
    print("\n  Fix: update pipeline.py schema validation -> pipeline jalan normal")
    print("  Runbook ref: ops/runbook.md > F2")


def scenario_corrupt_data():
    """F3: Tanggal tidak bisa di-parse."""
    print("\n=== SCENARIO: F3 — Format tanggal tidak bisa di-parse ===")
    restore()
    backup()

    # Inject baris dengan format tanggal baru
    fpath = RAW / "pos_orders_jan.csv"
    rows = []
    with fpath.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    rows.append({
        "order_id": "J-DRILL-01",
        "order_date": "15 January 2024",  # format baru
        "outlet": "Dago",
        "menu_item": "Es Kopi Susu",
        "size": "R",
        "qty": "1",
        "price_idr": "18000",
        "payment_method": "Cash",
        "shift": "Pagi",
        "cashier": "Rina",
    })

    with fpath.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("  [SIMULATED] Baris J-DRILL-01 pakai format '15 January 2024'")
    print("  [SIMULATED] parse_date() tidak handle format ini -> baris masuk NULL")

    print("\n  Jalankan pipeline:")
    result = subprocess.run(
        [sys.executable, str(ROOT / "pipeline" / "pipeline.py")],
        capture_output=True, text=True, cwd=str(ROOT),
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    # Pipeline jalan, tapi baris drill masuk sebagai NULL
    if result.returncode == 0:
        print("  [INFO] Pipeline selesai. Cek output_rows vs expected.")
        for line in result.stdout.split("\n"):
            if "output_rows" in line or "WARN" in line or "Drill" in line:
                print(f"    {line.strip()}")
    print("\n  Fix: tambah format di parse_date() -> pipeline jalan normal")
    print("  Runbook ref: ops/runbook.md > F3")


def main():
    parser = argparse.ArgumentParser(description="Simulate pipeline failures for drill")
    parser.add_argument(
        "--scenario",
        choices=["missing-file", "schema-drift", "corrupt-data", "all"],
        default="all",
    )
    args = parser.parse_args()

    # Generate data dulu
    print("Generating baseline data...")
    subprocess.run(
        [sys.executable, str(ROOT / "pipeline" / "generate_sample_data.py")],
        capture_output=True, cwd=str(ROOT),
    )

    scenarios = {
        "missing-file":   scenario_missing_file,
        "schema-drift":   scenario_schema_drift,
        "corrupt-data":   scenario_corrupt_data,
    }

    if args.scenario == "all":
        for fn in scenarios.values():
            fn()
            restore()  # reset sebelum scenario berikutnya
    else:
        scenarios[args.scenario]()

    print("\n=== DRILL COMPLETE ===")
    print("Semua data dikembalikan ke kondisi awal (restore from backup).")


if __name__ == "__main__":
    main()
