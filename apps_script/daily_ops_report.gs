/**
 * Daily Ops Report — PT KopiDate Indonesia
 *
 * Fungsi: dijalankan tiap pagi (jam 7) via Apps Script trigger.
 * Ambil data dari sheet "POS Log", hitung ringkasan harian,
 * lalu kirim email ke manajer.
 *
 * Struktur Sheet "POS Log":
 *   Kolom A: Tanggal      (format: dd/mm/yyyy)
 *   Kolom B: Outlet
 *   Kolom C: Total Order (integer)
 *   Kolom D: Revenue     (integer, Rupiah)
 *   Kolom E: Payment    (Cash/QRIS/e-wallet)
 *   Kolom F: Catatan
 *
 * Setup:
 *   1. Buka https://script.google.com -> New Script
 *   2. Paste seluruh file ini
 *   3. Run setup() sekali untuk bikin menu "POS Log" + trigger otomatis
 *   4. Atau manual: Edit > Current project's triggers > Add trigger > sendDailyReport, Time-driven, Day timer, 7-8 AM
 */

const CONFIG = {
  sheetName: "POS Log",
  emailTo: "manager@kopixyz.id",     // ganti dengan email nyata
  emailCc: "finance@kopixyz.id",     // opsional
  emailSubject: "Daily Ops Report — KopiDate",
  fromName: " KopiDate Automation",
};

// ─────────────────────────────────────────────────────────────────
// Setup
// ─────────────────────────────────────────────────────────────────

/**
 * Buat sheet "POS Log" di spreadsheet aktif + pasang trigger harian.
 * Jalankan SEKALI saja.
 */
function setup() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.sheetName) || ss.insertSheet(CONFIG.sheetName);

  // Header
  const headers = ["Tanggal", "Outlet", "Total Order", "Revenue (Rp)", "Payment", "Catatan"];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(1, 1, 1, headers.length)
    .setFontWeight("bold")
    .setBackground("#333333")
    .setFontColor("#ffffff");

  // Lebar kolom
  sheet.setColumnWidth(1, 120);  // Tanggal
  sheet.setColumnWidth(2, 120);  // Outlet
  sheet.setColumnWidth(3, 100);  // Total Order
  sheet.setColumnWidth(4, 130);  // Revenue
  sheet.setColumnWidth(5, 100);  // Payment
  sheet.setColumnWidth(6, 200);  // Catatan

  // Freeze header row
  sheet.setFrozenRows(1);

  // Pasang trigger harian jam 7 pagi
  ScriptApp.newTrigger("sendDailyReport")
    .timeBased()
    .atHour(7)
    .nearMinute(0)
    .everyDays(1)
    .create();

  Logger.log("Setup selesai. Trigger harian jam 7 AM aktif.");
}


// ─────────────────────────────────────────────────────────────────
// Core: kirim laporan harian
// ─────────────────────────────────────────────────────────────────

/**
 * Ambil data kemarin, hitung metrik, kirim email.
 * Dipanggil otomatis oleh trigger.
 */
function sendDailyReport() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.sheetName);

  if (!sheet) {
    Logger.log("Sheet '" + CONFIG.sheetName + "' tidak ditemukan.");
    return;
  }

  const yesterday = getYesterdayStr();
  const lastRow = sheet.getLastRow();

  if (lastRow <= 1) {
    Logger.log("Sheet kosong, tidak ada data untuk kemarin.");
    return;
  }

  // Ambil semua data (baris 2 onward)
  const data = sheet.getRange(2, 1, lastRow - 1, 6).getValues();

  // Filter baris kemarin
  const yesterdayRows = data.filter(function(row) {
    return row[0] !== "" && row[0] === yesterday;
  });

  if (yesterdayRows.length === 0) {
    Logger.log("Tidak ada data untuk tanggal " + yesterday);
    sendEmptyReport(yesterday);
    return;
  }

  // Aggregate per outlet
  const outletMap = {};
  yesterdayRows.forEach(function(row) {
    const outlet = String(row[1]).trim();
    if (!outlet) return;

    if (!outletMap[outlet]) {
      outletMap[outlet] = { orders: 0, revenue: 0 };
    }
    outletMap[outlet].orders  += parseInt(row[2]) || 0;
    outletMap[outlet].revenue += parseInt(row[3]) || 0;
  });

  const totalOrders = Object.values(outletMap)
    .reduce(function(s, v) { return s + v.orders; }, 0);
  const totalRevenue = Object.values(outletMap)
    .reduce(function(s, v) { return s + v.revenue; }, 0);
  const nOutlets = Object.keys(outletMap).length;

  const html = buildHtmlReport(yesterday, outletMap, totalOrders, totalRevenue, nOutlets);

  GmailApp.sendEmail(
    CONFIG.emailTo,
    CONFIG.emailSubject + " — " + yesterday,
    "",  // plain text fallback (kosong = html only)
    {
      htmlBody: html,
      cc: CONFIG.emailCc || "",
      name: CONFIG.fromName,
    }
  );

  Logger.log("Report terkirim untuk " + yesterday +
    ": " + totalOrders + " orders, Rp " + totalRevenue.toLocaleString("id-ID"));
}


/**
 * Kirim report meskipun tidak ada data ( supaya manager tahu sistem hidup).
 */
function sendEmptyReport(dateStr) {
  const html = "<p>Tidak ada data transaksi untuk <strong>" + dateStr +
    "</strong>. Cek apakah POS sudah dinyalakan atau koneksi berjalan normal.</p>" +
    "<p><em>Dikirim otomatis oleh KopiDate Automation</em></p>";

  GmailApp.sendEmail(
    CONFIG.emailTo,
    "[OpsAlert] Tidak ada data — " + dateStr,
    "",
    { htmlBody: html, name: CONFIG.fromName }
  );
}


// ─────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────

function getYesterdayStr() {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return Utilities.formatDate(d, Session.getScriptTimeZone(), "dd/MM/yyyy");
}

function fmtRupiah(n) {
  return "Rp " + Number(n).toLocaleString("id-ID");
}

function buildHtmlReport(dateStr, outletMap, totalOrders, totalRevenue, nOutlets) {
  const rows = Object.keys(outletMap).sort().map(function(outlet) {
    const v = outletMap[outlet];
    return "<tr><td>" + outlet + "</td><td style=\"text-align:right\">" +
      v.orders + "</td><td style=\"text-align:right\">" +
      fmtRupiah(v.revenue) + "</td><td style=\"text-align:right\">" +
      fmtRupiah(Math.round(v.revenue / v.orders)) + "</td></tr>";
  }).join("\n");

  return "<!DOCTYPE html><html><body style=\"font-family:Arial,sans-serif;" +
    "background:#f9f7f4;color:#222;max-width:600px;margin:0 auto;padding:20px\">" +
    "<h2 style=\"border-bottom:2px solid #6f4e37;padding-bottom:8px;color:#6f4e37\">" +
    "Daily Ops Report — " + dateStr +
    "</h2>" +
    "<table style=\"width:100%;border-collapse:collapse;margin-bottom:16px\">" +
    "<thead><tr style=\"background:#6f4e37;color:#fff\">" +
    "<th style=\"padding:8px;text-align:left\">Outlet</th>" +
    "<th style=\"padding:8px;text-align:right\">Order</th>" +
    "<th style=\"padding:8px;text-align:right\">Revenue</th>" +
    "<th style=\"padding:8px;text-align:right\">Avg Ticket</th>" +
    "</tr></thead><tbody>" + rows +
    "</tbody><tfoot style=\"background:#eee;font-weight:bold\">" +
    "<tr><td style=\"padding:8px\">TOTAL (" + nOutlets + " outlet)</td>" +
    "<td style=\"padding:8px;text-align:right\">" + totalOrders + "</td>" +
    "<td style=\"padding:8px;text-align:right\">" + fmtRupiah(totalRevenue) + "</td>" +
    "<td style=\"padding:8px;text-align:right\">" +
    fmtRupiah(Math.round(totalRevenue / totalOrders)) + "</td></tr>" +
    "</tfoot></table>" +
    "<p style=\"font-size:12px;color:#888\">" +
    "Dikirim otomatis via Google Apps Script · " + new Date().toLocaleString("id-ID") +
    "</p></body></html>";
}


// ─────────────────────────────────────────────────────────────────
// Debug / manual test
// ─────────────────────────────────────────────────────────────────

/**
 * Jalankan langsung untuk test tanpa tunggu trigger.
 * Run > sendDailyReport (debug)
 */
function debugReport() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(CONFIG.sheetName);
  if (!sheet) {
    Logger.log("Sheet belum ada. Jalankan setup() dulu.");
    return;
  }
  sendDailyReport();
}
