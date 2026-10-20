# Google Apps Script: Daily Ops Report

Mengisi gap: **Google Apps Script (JavaScript)**, **automasi laporan back-office**, Google Workspace advanced.

---

## Apa yang dilakukan

Script ini berjalan setiap pagi jam 7 AM secara otomatis (via Apps Script trigger):

1. Baca data dari sheet **"POS Log"** di spreadsheet aktif
2. Filter baris untuk tanggal kemarin
3. Aggregate per outlet: jumlah order + revenue + avg ticket
4. Kirim **HTML email** ke manajer & finance

---

## Struktur Sheet "POS Log"

Kolom harus persis seperti ini:

| Kolom | Nama       | Format              |
|-------|------------|---------------------|
| A     | Tanggal    | `dd/mm/yyyy`        |
| B     | Outlet     | Dago / Setiabudi / Buah Batu |
| C     | Total Order| Integer             |
| D     | Revenue    | Integer (Rupiah)    |
| E     | Payment    | Cash / QRIS / GoPay / OVO |
| F     | Catatan    | Teks (optional)     |

---

## Setup (jalankan sekali)

1. Buka https://script.google.com
2. New Project -> paste isi `daily_ops_report.gs`
3. Run -> **setup()** -> Authorize -> selesai

`setup()` akan:
- Buat sheet "POS Log" + header
- Auto-size kolom
- Freeze header row
- **Pasang trigger harian jam 7 AM**

---

## Test (tanpa tunggu trigger)

1. Buka Apps Script project
2. Run -> **debugReport()**
3. Cek email

---

## Variabel yang harus diedit sebelum deploy

```javascript
const CONFIG = {
  sheetName:    "POS Log",
  emailTo:      "manager@kopixyz.id",   // <- ganti
  emailCc:      "finance@kopixyz.id",  // <- atau hapus
  emailSubject: "Daily Ops Report - KopiDate",
  fromName:     "KopiDate Automation",
};
```

---

## Output email (HTML)

```
Daily Ops Report — 19/10/2024
---------------------------------
Outlet        Order  Revenue      Avg Ticket
Dago            47    Rp 1.919.700   Rp 40.845
Setiabudi       43    Rp 1.677.100   Rp 38.999
Buah Batu       48    Rp 1.831.300   Rp 38.152
---------------------------------
TOTAL (3)      138   Rp 5.428.100   Rp 39.334

Dikirim otomatis via Google Apps Script
```

---

## Caveat / limitasi

- **Tanpa data:** kirim "OpsAlert" email supaya manager tahu sistem hidup
- **Format tanggal harus konsisten `dd/mm/yyyy`** — kalau POS export beda, tambah parsing di `getYesterdayStr()`
- **Tidak handle merge cell** — sheet harus flat
- **Scales** ke 1 sheet, 1 spreadsheet — kalau multi-branch, perlu `SpreadsheetApp.openById()` per outlet

---

## Relevance ke jobdesk KopiDate

Ini persis contoh dari jobdesk:

> "Mengotomasi laporan back-office rutin, termasuk melalui Google Apps Script."

Contoh nyata ini menunjukkan Anda tahu:
- Apps Script syntax (JavaScript)
- Spreadsheet manipulation
- Gmail integration
- Trigger automation
- Error handling (empty report case)
