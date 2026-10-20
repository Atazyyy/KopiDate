"""
Generate realistic dirty POS data for PT KopiDate Indonesia demo.

Run: python generate_sample_data.py
Output: 3 files in data/raw/
  - pos_orders_jan.csv      dirty POS export (Order #1, Januari)
  - pos_orders_feb.csv      dirty POS export (Order #2, Februari)
  - sheets_export.csv       Google Sheets manual entry (format berbeda)
  - master_menu.csv         master data menu (clean)

Dirty data yang di-inject (representatif untuk masalah data POS nyata):
- Typo & inkonsistensi case: "Qris", "gopay", "GOPAY ", "OFO"
- Whitespace tersembunyi: "Dago ", "  Setiabudi"
- Format tanggal beda: "2024-01-15" vs "15/01/2024" vs "15-01-24"
- Missing values: payment_method kosong, shift kosong
- Variant nama size: "R", "r", "Reg", "REGULAR", "Reguler"
- Duplicate order_id
- Price yang tidak match dengan master menu (sumber: diskon/offline edit)
- qty negatif / 0 (sumber: void/cancel entry tapi ID-nya masih di-export)
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)  # reproducibility

OUTLETS = ["Dago", "Setiabudi", "Buah Batu"]

MENU = [
    # (name, category, base_price, sizes)
    ("Es Kopi Susu", "Signature", 18000, ["R", "L"]),
    ("Kopi Tubruk", "Classic", 12000, ["R", "L"]),
    ("Kopi Sanger", "Classic", 15000, ["R", "L"]),
    ("Kopi Hitam", "Classic", 10000, ["R", "L"]),
    ("Americano", "Espresso", 20000, ["R", "L", "XL"]),
    ("Cappuccino", "Espresso", 22000, ["R", "L", "XL"]),
    ("Cafe Latte", "Espresso", 22000, ["R", "L", "XL"]),
    ("Cafe Mocha", "Espresso", 25000, ["R", "L"]),
    ("Cold Brew", "Specialty", 28000, ["R", "L"]),
    ("Kopi Luwak", "Premium", 35000, ["R"]),
    ("Kopi Ginseng", "Signature", 18000, ["R", "L"]),
    ("Kopi Tarik", "Signature", 16000, ["R", "L"]),
    ("Vietnamese Coffee", "Specialty", 24000, ["R", "L"]),
    ("Affogato", "Dessert", 30000, ["R"]),
    ("Tubruk Jahe", "Classic", 14000, ["R", "L"]),
]

PAYMENTS_CLEAN = ["Cash", "QRIS", "GoPay", "OVO", "Dana", "ShopeePay", "Debit"]
SHIFTS = ["Pagi", "Siang", "Malam"]
CASHIERS = ["Rina", "Andi", "Budi", "Sari", "Dedi", "Maya", "Agus"]


def rand_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def shift_for_hour(h: int) -> str:
    if 6 <= h < 12:
        return "Pagi"
    if 12 <= h < 18:
        return "Siang"
    return "Malam"


def dirty_payment(p: str) -> str:
    variants = {
        "QRIS": ["Qris", "QRIS ", " qris", "QRIS"],
        "GoPay": ["gopay", "GOPAY", "GoPay ", "Gopay"],
        "OVO": ["ovo", "OFO", "OVO "],
        "Dana": ["DANA", "dana"],
        "ShopeePay": ["ShopeePay ", "Shopeepay"],
        "Debit": ["debit", "DEBIT"],
        "Cash": ["cash", "CASH "],
    }
    if p in variants and random.random() < 0.18:
        return random.choice(variants[p])
    return p


def dirty_outlet(o: str) -> str:
    if random.random() < 0.10:
        variations = [
            lambda x: x + " ",
            lambda x: " " + x,
            lambda x: x.lower(),
            lambda x: x.upper(),
        ]
        return random.choice(variations)(o)
    return o


def dirty_size(s: str) -> str:
    variants = {
        "R": ["r", "Reg", "REGULAR", "Reguler", " reguler"],
        "L": ["l", "Large", "LARGE", "besar"],
        "XL": ["xl", "X-Large", "Extra Large"],
    }
    if s in variants and random.random() < 0.20:
        return random.choice(variants[s])
    return s


def size_multiplier(s: str) -> float:
    if s in ("R", "r", "Reg", "REGULAR", "Reguler", " reguler"):
        return 1.0
    if s in ("L", "l", "Large", "LARGE", "besar"):
        return 1.3
    if s in ("XL", "xl", "X-Large", "Extra Large"):
        return 1.6
    return 1.0


def dirty_date(d: date) -> str:
    # 3 format campur
    fmt = random.choice(["iso", "id_short", "dot", "verbose"])
    if fmt == "iso":
        return d.strftime("%Y-%m-%d")
    if fmt == "id_short":
        return d.strftime("%d/%m/%Y")
    if fmt == "dot":
        return d.strftime("%d.%m.%y")
    return d.strftime("%d %b %Y")


def price_for(menu_item: str, size: str) -> int:
    for name, _, base, _ in MENU:
        if name == menu_item:
            return int(base * size_multiplier(size))
    return 0


def generate_pos_orders(start: date, end: date, n_rows: int, order_prefix: str) -> list[dict]:
    rows = []
    for i in range(1, n_rows + 1):
        d = rand_date(start, end)
        h = random.choices([8, 9, 10, 13, 14, 15, 19, 20], k=1)[0]
        shift = shift_for_hour(h)
        menu_name, _, _, sizes = random.choice(MENU)
        size = random.choice(sizes)
        qty = random.choices([1, 1, 1, 2, 3], k=1)[0]
        if random.random() < 0.01:
            qty = -1  # void entry
        elif random.random() < 0.01:
            qty = 0

        price = price_for(menu_name, size)
        # 2% price mismatch (discount/manual edit di kasir)
        if random.random() < 0.02:
            price = max(0, price + random.choice([-2000, -1000, 1000]))

        payment = random.choice(PAYMENTS_CLEAN)
        if random.random() < 0.04:
            payment = ""  # missing
        else:
            payment = dirty_payment(payment)

        outlet = dirty_outlet(random.choice(OUTLETS))
        cashier = random.choice(CASHIERS)

        rows.append({
            "order_id": f"{order_prefix}-{i:04d}",
            "order_date": dirty_date(d),
            "outlet": outlet,
            "menu_item": menu_name,
            "size": dirty_size(size),
            "qty": qty,
            "price_idr": price,
            "payment_method": payment,
            "shift": shift,
            "cashier": cashier,
        })

    # inject 2 duplicates
    dup_idx = random.sample(range(n_rows), 2)
    for idx in dup_idx:
        rows.append({**rows[idx]})

    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Master menu (clean)
    menu_fields = ["menu_item", "category", "base_price_idr", "sizes_available"]
    menu_rows = [
        {
            "menu_item": name,
            "category": cat,
            "base_price_idr": price,
            "sizes_available": ",".join(sizes),
        }
        for name, cat, price, sizes in MENU
    ]
    write_csv(out_dir / "master_menu.csv", menu_rows, menu_fields)

    # POS orders Jan + Feb
    pos_fields = [
        "order_id", "order_date", "outlet", "menu_item", "size",
        "qty", "price_idr", "payment_method", "shift", "cashier",
    ]
    pos_jan = generate_pos_orders(date(2024, 1, 1), date(2024, 1, 31), 180, "J")
    pos_feb = generate_pos_orders(date(2024, 2, 1), date(2024, 2, 28), 200, "F")
    write_csv(out_dir / "pos_orders_jan.csv", pos_jan, pos_fields)
    write_csv(out_dir / "pos_orders_feb.csv", pos_feb, pos_fields)

    # Google Sheets export — format berbeda
    # Header Indonesia, separator berbeda, kolom beda nama, ada kolom extra
    sheets_fields = [
        "ID Pesanan", "Tanggal", "Outlet", "Item", "Ukuran",
        "Jumlah", "Harga Total", "Metode Bayar", "Catatan",
    ]
    sheets_rows = []
    # ambil subset dari Jan + Feb sebagai "data yang diinput manual via Sheets"
    pool = random.sample(pos_jan + pos_feb, 80)
    for r in pool:
        catatan = []
        if r["qty"] < 0:
            catatan.append("VOID")
        if random.random() < 0.1:
            catatan.append("diskon manual")
        sheets_rows.append({
            "ID Pesanan": r["order_id"],
            "Tanggal": r["order_date"],
            "Outlet": r["outlet"],
            "Item": r["menu_item"],
            "Ukuran": r["size"],
            "Jumlah": r["qty"],
            "Harga Total": r["price_idr"],
            "Metode Bayar": r["payment_method"],
            "Catatan": "; ".join(catatan) if catatan else "",
        })
    write_csv(out_dir / "sheets_export.csv", sheets_rows, sheets_fields)

    print(f"Generated:")
    print(f"  - {out_dir / 'master_menu.csv'} ({len(menu_rows)} rows)")
    print(f"  - {out_dir / 'pos_orders_jan.csv'} ({len(pos_jan)} rows)")
    print(f"  - {out_dir / 'pos_orders_feb.csv'} ({len(pos_feb)} rows)")
    print(f"  - {out_dir / 'sheets_export.csv'} ({len(sheets_rows)} rows)")


if __name__ == "__main__":
    main()
