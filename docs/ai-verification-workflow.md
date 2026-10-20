# AI-Assisted Development Workflow

Mengisi gap: **Claude Code sebagai daily tool**, **verifikasi hasil AI sebelum production**.

---

## Prinsip

> "Menggunakan Git setiap hari (branch, commit, pull request, review) dan **memverifikasi setiap hasil AI sebelum digunakan.**"
> — KopiDate jobdesk

AI coding assistant mempercepat penulisan, tapi:
1. AI hallucinate — nama kolom, syntax, kondisi edge case
2. AI tidak tahu konteks bisnis spesifik (misal: format tanggal Indonesia)
3. AI output butuh judgment manusia sebelum masuk production

Workflow ini memastikan setiap baris code yang ditulis oleh AI sudah melalui review.

---

## Proses Standar: Branch -> AI -> Review -> PR -> Merge

```
1. Create branch     git switch -c feat/fix-payment-validation
2. AI generate       Claude Code: "tulis fungsi validate_payment()"
3. Self-review       Baca setiap baris, cek:
                     - Nama kolom cocok dengan schema?
                     - Edge case (null, empty string, typo)?
                     - Business logic masuk akal?
4. Write test       python -m pytest tests/ -v
5. Commit            git add . && git commit -m "feat: add payment validation"
6. Push + PR         git push -u origin HEAD
7. PR description    Jelaskan apa yang AI generate, apa yang diubah manual
8. Merge / close PR  Setelah tested & reviewed
```

---

## 3 Contoh dari repo ini

### Contoh 1: Generate SQL Query — verifikasi pakai EXPLAIN + sample data

**Task:** "Buatkan query SQL untuk top 5 menu per outlet"

```sql
-- AI generate (Claude Code):
SELECT outlet, menu_item, SUM(revenue_idr) AS revenue
FROM orders
GROUP BY outlet, menu_item
ORDER BY revenue DESC
LIMIT 5;
```

**Review yang dilakukan:**
1. Jalankan dengan `EXPLAIN` dulu — cek plan tanpa execute
2. Test di sample data kecil — hasilnya masuk akal?
3. CROSS-CHECK: ada outlet yang hilang? Limit 5 global, bukan per outlet!
4. Fix: pakai `ROW_NUMBER()` window function (lihat `queries.sql` Q4)

**Commit message:**
```
fix: top-menu query — use ROW_NUMBER per outlet not global LIMIT

AI-generated query had global LIMIT 5, missing per-outlet ranking.
Corrected with window function. Tested against KopiDate.duckdb sample.
```

---

### Contoh 2: Generate Apps Script — review baris per baris

**Task:** "Buatkan script kirim email harian"

```javascript
// AI generate — ada bug:
GmailApp.sendEmail(to, subject, body);  // ← body plain text

// Self-review:
// - body string, bukan htmlBody param → email mentah
// - tidak ada error handling kalau sheet kosong
// - timezone tidak di-hardcode → bisa salah jam
```

**Fix sebelum commit:**
```javascript
GmailApp.sendEmail(to, subject, "", { htmlBody: body });  // html only
if (lastRow <= 1) return;  // handle empty sheet
const tz = Session.getScriptTimeZone();  // explicit timezone
```

---

### Contoh 3: Generate Data Cleaning Logic — test edge case manual

**Task:** "Normalisasi payment method dari CSV"

```python
# AI generate:
payment = payment.upper().strip()  # → "GOPAY" akan jadi "GOPAY" (benar?)

# Self-review:
# - Payment canonical list: GoPay (capital G + P), bukan GOPAY
# - "gopay" → "GOPAY" → tidak match "GoPay"
# - Fix: pakai exact match dict, bukan uppercase
```

```python
# Fixed:
PAYMENT_CANONICAL = {"Cash", "QRIS", "GoPay", "OVO", "Dana", "ShopeePay", "Debit"}
def normalize_payment(s):
    if pd.isna(s) or not s.strip():
        return None
    for canon in PAYMENT_CANONICAL:
        if s.strip().lower() == canon.lower():
            return canon
    return None
```

---

## Checklist sebelum commit code yang di-generate AI

- [ ] Baca dari atas ke bawah, garis per garis — jangan skip
- [ ] Cek nama kolom / nama field — cocok dengan schema/dokumentasi?
- [ ] Edge case: null, empty string, 0, negative, duplicate?
- [ ] Run test, atau jalankan query di sample data
- [ ] Cek business logic — masuk akal untuk konteks?
- [ ] Commit message menyebut "AI-generated" + perubahan manual yang dilakukan
- [ ] Tidak ada credential / secret hardcoded

---

## Commit Message Konvensi

```
<type>: <apa yang dilakukan>

AI-generated: <ringkasan apa yang AI tulis>
Reviewed: <apa yang diubah manual>
Tested: <cara di-tes>
```

Contoh:
```
feat: daily ops report via Apps Script

AI-generated: auto-email dari sheet POS Log setiap pagi
Reviewed: tambah error handling (sheet kosong, no data yesterday),
         fix body vs htmlBody param
Tested: debugReport() manual — email masuk ke test inbox
```

---

## Relevance ke interview KopiDate

> "Terbiasa menggunakan AI coding assistant seperti Claude Code, Copilot, Cursor, atau sejenisnya
> serta **mampu mengevaluasi dan memperbaiki hasil AI yang keliru.**"

Ini menunjukkan:
- Anda tidak blindly trust AI output
- Anda punya proses review yang reproducible
- Anda bisa jelaskan BAHKAN JIKA ANDA PERNAH MENOLAK output AI dan mengapa
