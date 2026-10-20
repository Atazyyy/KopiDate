# Operational Runbook — Pipeline Failure Procedures

Mengisi gap: **reliability mindset**, **"memperbaiki dengan cepat saat kegagalan"**, production systems.

---

## Prinsip Dasar

> "Menjalankan dan memelihara pipeline data harian; **memperbaikinya dengan cepat saat terjadi kegagalan.**"

Kalau pipeline down, angka dashboard salah. Orang mengambil keputusan dari angka itu. Jadi speed-to-fix penting, tapi **yang lebih penting**: jangan fix asal-asalan.

---

## Failure Matrix

### F1: POS Export file tidak ada / tidak ditemukan

**Gejala:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/pos_orders_jan.csv'
```

**Diagnosis:**
1. Apakah file benar-benar tidak ada di folder?
2. Apakah nama file berubah? (misal: `pos_orders_jan_2024.csv`)
3. Apakah pipeline dijalankan dari direktori yang benar?

**Fix:**
```bash
ls -la data/raw/
# Kalau file ada tapi nama beda
mv data/raw/pos_orders_jan_2024.csv data/raw/pos_orders_jan.csv
python pipeline/generate_sample_data.py
python pipeline/pipeline.py
```

**Pencegahan:** Commit naming convention ke README. Jangan rename file yang sudah ada di version control.

---

### F2: Kolom baru di export POS (schema drift)

**Gejala:**
```
KeyError: 'payment_method'
```

**Diagnosis:**
1. Apakah POS di-upgrade dan menambah/mengubah kolom?
2. Apakah header CSV berubah?

**Fix:**
```python
EXPECTED = {"order_id", "order_date", "outlet", "menu_item", "size",
            "qty", "price_idr", "payment_method", "shift", "cashier"}
actual = set(pd.read_csv("data/raw/pos_orders_jan.csv", nrows=1).columns)
new_cols = actual - EXPECTED
if new_cols:
    print(f"WARNING: kolom baru terdeteksi: {new_cols}")
    raise ValueError(f"Schema drift: {new_cols}")
```

---

### F3: Tanggal tidak bisa di-parse

**Gejala:**
```
ValueError: unconverted data remains: /2024
```
Atau: semua baris masuk sebagai `NULL` di kolom `order_date`.

**Fix:**
Tambah format baru di `parse_date()` di `pipeline.py`. Contoh: `"%d %B %Y"`.

---

### F4: Data Duplikat — ID sama tapi nilai beda

Ini **data conflict**, bukan duplicate biasa. Perlu review manusia.

```
J-0042  Cold Brew   Rp 28.000   <- original
J-0042  Cold Brew   Rp 30.000   <- conflict
```

**Fix:**
```
1. Export conflict rows ke review_conflicts.csv
2. Tanya kasir / manager: mana yang benar?
3. Decision: hapus baris yang salah
4. Update pipeline: tambah step deteksi konflik sebelum dedup
```

---

### F5: DuckDB file corrupted / locked

**Gejala:**
```
duckdb.IOException: Permission denied
```

**Fix:**
```bash
rm pipeline/KopiDate.duckdb
python pipeline/pipeline.py
```

---

### F6: Dashboard angka tidak cocok dengan pipeline output

**Fix:**
```bash
python pipeline/pipeline.py
# Cek cleansing report — input_rows vs output_rows
# Kalau output_rows turun drastis, cleansing rule terlalu agresif
```

---

## Alert / Monitoring Checklist (production)

- Cron menjalankan `pipeline.py` setiap pagi jam 5 AM
- Notifikasi kalau pipeline gagal (email / Slack)
- Notifikasi kalau cleansing report menunjukkan > 10% rows ter-drop
- Dashboard auto-refresh setelah pipeline selesai
- Log pipeline run (timestamp + status + row count)

---

## Recovery Time Target

| Severity | Definisinya                     | Target Fix |
|----------|--------------------------------|-----------|
| P1       | Pipeline tidak jalan sama sekali | 30 menit  |
| P2       | Angka berbeda dari expectation  | 2 jam     |
| P3       | Warning (kolom baru terdeteksi) | 1 hari    |

P1 = fix sekarang, baru dokumentasi. P3 = dokumentasi dulu, fix sprint berikutnya.
