# Data Dictionary — KopiDate POS Data

## Tabel: `orders` (tabel fakta)

| Field            | Tipe      | Deskripsi                                      | Contoh                          |
|------------------|-----------|------------------------------------------------|---------------------------------|
| `order_id`       | VARCHAR   | ID unik transaksi. Format: `{bulan}-{urutan}`  | `J-0042`, `F-0091`             |
| `order_date`      | DATE      | Tanggal transaksi (YYYY-MM-DD, sudah dinormalisasi) | `2024-01-21`              |
| `outlet`         | VARCHAR   | Outlet tempat transaksi. Salah satu: `Dago`, `Setiabudi`, `Buah Batu` | `Dago`              |
| `menu_item`      | VARCHAR   | Nama menu (harus ada di tabel `menu`)         | `Es Kopi Susu`, `Cold Brew`     |
| `size`           | VARCHAR   | Ukuran: `R` (Regular), `L` (Large), `XL`      | `R`, `L`                       |
| `qty`            | INTEGER   | Jumlah item. Selalu > 0. Void/cancel di-drop. | `1`, `2`, `3`                  |
| `price_idr`      | INTEGER   | Harga per item (Rupiah). Sudah di-repair dari master menu. | `18000`, `23400`         |
| `revenue_idr`    | INTEGER   | `qty * price_idr`. Total revenue per baris.   | `18000`, `36000`                |
| `payment_method` | VARCHAR   | Metode bayar. Salah satu: `Cash`, `QRIS`, `GoPay`, `OVO`, `Dana`, `ShopeePay`, `Debit` | `QRIS`              |
| `shift`          | VARCHAR   | Shift kerja. Salah satu: `Pagi` (06-12), `Siang` (12-18), `Malam` (18-06). NULL = data dari Sheets export. | `Pagi` |
| `cashier`        | VARCHAR   | Nama kasir. NULL = data dari Sheets export.    | `Rina`, `Andi`                  |
| `__source`       | VARCHAR   | Sumber data: `pos` = POS export, `sheets` = Google Sheets manual entry | `pos`                 |

---

## Tabel: `menu` (tabel dimensi)

| Field             | Tipe      | Deskripsi                               | Contoh                   |
|-------------------|-----------|-----------------------------------------|--------------------------|
| `menu_item`       | VARCHAR   | Nama menu (primary key, harus sama dengan `orders.menu_item`) | `Kopi Tubruk` |
| `category`        | VARCHAR   | Kategori: `Signature`, `Classic`, `Espresso`, `Specialty`, `Premium`, `Dessert` | `Classic` |
| `base_price_idr`  | INTEGER   | Harga ukuran Regular (R) dalam Rupiah.  | `12000`, `22000`         |
| `sizes_available` | VARCHAR  | Ukuran yang tersedia, comma-separated.  | `R,L`, `R,L,XL`          |

---

## Konvensi Penamaan

- **ID transaksi:** `{bulan}-{urutan 4 digit}`. Prefix `J` = Januari, `F` = Februari. Tidak ada data duplikasi ID antar-bulan.
- **Tanggal:** selalu `YYYY-MM-DD` di warehouse (setelah parsing).
- **Outlet:** capitalize setiap kata (`Dago`, `Setiabudi`, `Buah Batu`).
- **Price:** selalu integer Rupiah, tidak ada desimal.
- **Size:** selalu `R`, `L`, atau `XL` (tidak ada lowercase, tidak ada alias lain di warehouse).

---

## Batasan / Assumptions

- Tidak ada timezone di data — semua diasumsikan Asia/Jakarta (UTC+7)
- Tidak ada diskon tersimpan sebagai field — kalau price mismatch, di-repair pakai master (lihat cleansing-decisions.md)
- Void/cancel (`qty <= 0`) di-drop, tidak masuk warehouse. Untuk audit, perlu tabel `orders_voided` terpisah.
- Master menu adalah sumber kebenaran untuk price. Kalau master tidak cocok dengan harga kasir, yang dimenangkan adalah master.
