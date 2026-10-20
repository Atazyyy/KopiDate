# Cleansing Decision Log

Setiap keputusan dicatat dengan alasannya — supaya bisa diaudit dan direview.

---

## 1. Order ID kosong → DROP

**Aturan:** Baris tanpa `order_id` dibuang.
**Alasan:** `order_id` adalah primary key. Baris tanpa itu tidak bisa di-trace, di-reconcile, atau di-audit. Data POS yang kehilangan ID = data yang hilang.
**Risiko:** Data hilang permanen. Mitigasi: jumlah baris dibuang selalu di-report di cleansing report.

---

## 2. Duplicate order_id → KEEP FIRST

**Aturan:** Kalau `order_id` sama persis muncul beberapa kali, simpan yang pertama (`drop_duplicates(keep='first')`).
**Alasan:** Di demo ini, 80 baris `sheets_export.csv` adalah copy manual dari baris yang sudah ada di POS export. Double-counting revenue = angka dashboard salah. Ini skenario nyata: tim isi ulang manual ke Sheets data yang sudah otomatis masuk dari POS.
**Catatan:** Kalau selisihnya bukan duplicate identik tapi *duplicate dengan nilai berbeda*, itu konflik data — harus masuk review list, bukan auto-drop. Pipeline ini belum handle konflik; lihat `ops/runbook.md`.

---

## 3. Outlet tidak dikenal → DROP

**Aturan:** Outlet harus salah satu dari `{Dago, Setiabudi, Buah Batu}` (case/whitespace-insensitive).
**Alasan:** Outlet baru yang belum masuk master data = data yang belum diverifikasi. Lebih baik hilang dari report daripada muncul sebagai outlet typo yang bikin pivot table salah.
**Normalisasi:** `strip()` + `.title()` → `" Dago"` dan `"DAGO"` keduanya jadi `"Dago"`.

---

## 4. Payment method tidak dikenal → DROP

**Aturan:** Payment harus salah satu dari `{Cash, QRIS, GoPay, OVO, Dana, ShopeePay, Debit}`.
**Alasan:** Ini kolom yang dipakai Finance & BD untuk rekonsiliasi. Metode yang tidak dikenal = uang yang tidak bisa ditelusuri. 10 baris di-drop karena `"OFO"` (typo OVO) di luar daftar.
**Normalisasi:** case-insensitive exact match → `"gopay"` dan `"GOPAY "` → `"GoPay"`.
**Peringatan:** Ini *bukan* Ini *bukan* fuzzy matching. Kalau nanti ada `"OVO Payment"` atau `"OVO QRIS"`, itu perlu master mapping baru, bukan tebakan.

---

## 5. Ukuran tidak dikenal → DROP

**Aturan:** Size harus R / L / XL.
**Alasan:** Size menentukan harga. Size yang tidak dikenal = harga yang tidak bisa divalidasi.
**Normalisasi:** Mapping eksplisit, bukan `.upper()`:
```
"r" → "R"    "Reg" → "R"      "REGULAR" → "R"    "Reguler" → "R"
"l" → "L"    "Large" → "L"    "LARGE" → "L"      "besar" → "L"
"xl" → "XL"  "X-Large" → "XL" "Extra Large" → "XL"
```
Mapping ini di-code di `pipeline.py` sebagai `SIZE_NORMALIZE` — **bukan** tebakan runtime. Kalau ada size variant baru, mapping-nya ditambah di sana dan di-review.

---

## 6. Menu item tidak dikenal → DROP

**Ataran:** Menu harus match persis dengan `master_menu.csv`.
**Alasan:** Master data adalah sumber kebenaran. Item yang tidak ada di master = item eksperimen atau typo.
**Keterbatasan:** Pipeline ini masih case-sensitive untuk menu item. Kalau nanti ada `"ES KOPI SUSU"` di POS, itu akan ter-drop. Fix-nya: normalisasi case juga untuk menu. *Belum dikerjakan — catat sebagai TODO.*

---

## 7. qty <= 0 → DROP

**Aturan:** `qty` harus integer > 0.
**Alasan:** `qty = -1` = void/cancel entry yang ID-nya masih ikut ke-export. `qty = 0` = placeholder. Keduanya bukan transaksi. 6 baris ter-drop di demo ini.
**Catatan:** Untuk audit yang lebih ketat, baris ini sebaiknya *tidak* langsung drop tapi masuk tabel `orders_voided` supaya Finance bisa lihat ada void. *Belum dikerjakan — TODO.*

---

## 8. Price tidak match master → RECOMPUTE

**Aturan:** `expected_price = base_price_idr × size_multiplier`, dengan multiplier R=1.0, L=1.3, XL=1.6. Kalau `price_idr` di POS tidak sama, pakai hasil recompute.
**Alasan:** Ini 9 baris di demo. Sumbernya: kasirapply diskon manual, atau harga berubah di POS tapi master belum di-update.
**Pertanyaan bisnis yang belum dijawab:** *Apakah diskon manual itu valid?* Kalau valid, `price_idr` asli lebih benar dan yang salah adalah master. Kalau tidak valid, recompute benar.
**Status:** Pipeline ini meng-*repair* price agar angka revenue konsisten, tapi **tidak** menandai baris yang diperbaiki. Untuk production, ini harus jadi review queue, bukan silent fix. *Ini limitasi yang saya acknowledge.*

---

## 9. Format tanggal → PARSE ke DATE

**Aturan:** Coba 4 format berurutan, ambil yang pertama cocok.
```
2024-01-15     (ISO — default sistem POS)
15/01/2024      (Indonesia)
15.01.24        (dot + 2-digit year)
15 Jan 2024     (verbose)
```
**Alasan:** Sistem POS, input manual, dan Google Sheets masing-masing bisa beda format. Kalau tidak diparse ke satu tipe, agregasi per tanggal tidak mungkin dilakukan.
**Risiko:** `15.01.24` bisa ambigu (15 Januari 2024 atau 1 Februari 2024?). Pipeline ini mengasumsikan format Indonesia (DD.MM.YY). Ini asumsi yang harus dikonfirmasi dengan tim operasional.

---

## 10. Shift kosong dari Sheets → BIARKAN NULL

**Aturan:** Baris dari `sheets_export.csv` tidak punya kolom shift → `NULL`.
**Alasan:** Tidak mengarang data. Query yang butuh shift harus handle NULL (lihat `queries.sql` query #5 dengan `WHERE shift IS NOT NULL`).
**Jangan:** mengisi dengan "default" atau menebak dari jam — tidak ada dasar untuk itu.

---

## Yang SENGAJA tidak dikerjakan

Hal-hal ini di luar scope demo, tapi relevan untuk production:

- **Fuzzy matching** menu item (Levenshtein / difflib) — berisiko salah match lebih besar daripada yang diselesaikan
- **Auto-detect encoding** file POS — asumsinya UTF-8
- **Timezone handling** — semua timestamp diasumsikan Asia/Jakarta
- **Conflict resolution** untuk duplicate dengan nilai berbeda — butuh human review
- **Incremental load** — pipeline ini full-refresh, delete-all-then-insert
- **Schema drift detection** — kalau POS tambah kolom, pipeline tidak akan complain

Semua ini ada di `ops/runbook.md` sebagai procedure kalau terjadi.