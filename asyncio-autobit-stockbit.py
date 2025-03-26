import asyncio
import json
import os
import os
import datetime
import subprocess
import time
import socket
import math
import re
from playwright.async_api import async_playwright

# ============================
# 🔧 KONFIGURASI LOGGING & PATH
# ============================
CONFIG_PATH = "D:/wildan/config-json/config.json"
LOG_DIR = "D:/wildan/log-activity"
SCREENSHOT_DIR = "D:/wildan/screener-capture"
PRODUCT_SCREENSHOT_DIR = "D:/wildan/produk-screenshoot"
ORDER_SCREENSHOT_DIR = "D:/wildan/order-screen-shoot"
CHROME_DEBUGGER_URL = "http://127.0.0.1:9222"
STOCKBIT_URL = "https://stockbit.com/screener"
LOGIN_URL = "https://stockbit.com/login"
CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"


# Alert VBS
VBS_ALERT_PATH = "D:\\wildan\\alert\\alert.vbs"

# Buat folder jika belum ada
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(ORDER_SCREENSHOT_DIR, exist_ok=True)

# ============================
# 🔧 FUNGSI LOGGING
# ============================
def get_log_file():
    today = datetime.datetime.now().strftime('%d%m%Y')
    return f"{LOG_DIR}/{today}.log"

def log(status, message, category=None):
    """Mencetak log ke terminal dan menyimpannya ke file dengan pembatas kategori."""
    timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    log_message = f"{timestamp} {status} {message}"

    if category:
        if category not in log.categories:
            log.categories.add(category)
            separator = "\n" + "=" * 30 + f"\n{category.upper()}\n" + "-" * 30
            print(separator)
            with open(get_log_file(), "a", encoding="utf-8") as log_file:
                log_file.write(separator + "\n")

    print(log_message)
    with open(get_log_file(), "a", encoding="utf-8") as log_file:
        log_file.write(log_message + "\n")

log.categories = set()  # Menyimpan kategori log agar tidak duplikat

# ============================
# 🚀 CEK & JALANKAN CHROME DEBUGGING
# ============================
def is_port_open(host, port):
    """Memeriksa apakah port debugging Chrome terbuka."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0

def start_chrome_debugging():
    """Memastikan Chrome Debugging Mode berjalan sebelum koneksi Playwright."""
    if is_port_open("127.0.0.1", 9222):
        log("✅", "Chrome Debugging Mode sudah aktif!", "LOG CHROME DEBUGGING")
        return

    log("⚠️", "Google Chrome 'Debugging' belum aktif! Menjalankan Chrome secara debugging...", "LOG CHROME DEBUGGING")
    
    subprocess.Popen([
        CHROME_PATH, 
        "--remote-debugging-port=9222", 
        "--user-data-dir=C:\\chrome-profile", 
        "--disable-popup-blocking"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for _ in range(10):  # Coba 10 kali dengan delay 1 detik
        time.sleep(1)
        if is_port_open("127.0.0.1", 9222):
            log("✅", "Chrome Debugging Mode telah aktif!", "LOG CHROME DEBUGGING")
            return

    log("❌", "Gagal menjalankan Chrome Debugging Mode! Menampilkan alert VBS.", "LOG CHROME DEBUGGING")
    subprocess.run(["wscript", VBS_ALERT_PATH])
    exit()

# Pastikan Chrome Debugging aktif sebelum menjalankan Playwright
start_chrome_debugging()

# ============================
# ✅ PASTIKAN USER SUDAH LOGIN
# ============================
async def check_login(page):
    """Memeriksa apakah user sudah login ke Stockbit."""
    if page.url.startswith(LOGIN_URL):
        log("⚠️", "User belum login! Menampilkan popup peringatan.", "LOG CEK LOGIN USER")
        subprocess.run(["wscript", VBS_ALERT_PATH])
        log("❌", "Proses dihentikan. Silakan login terlebih dahulu.", "LOG CEK LOGIN USER")
        return False
    return True

# ============================
# ✅ PASTIKAN HALAMAN SCREENER SELESAI LOAD
# ============================
async def ensure_screener_ready(page):
    """Memastikan halaman Screener termuat sempurna sebelum proses berlanjut."""
    try:
        log("⏳", "Menunggu halaman Screener termuat...", "LOG PADA MEMBACA DATA SCREENER YANG AKTIF")

        # Tunggu elemen utama tabel Screener
        screener_table = page.locator("div.sc-6f84e760-3.gXCJki")
        await screener_table.wait_for(state="visible", timeout=10000)

        # Ambil nama screener
        screener_name = await page.locator("input[name='screenName']").get_attribute("value")
        if not screener_name:
            screener_name = "UNKNOWN"

        # Hitung jumlah saham yang ditemukan
        rows = await page.locator("tbody tr:not([aria-hidden='true'])").all()
        total_saham = len(rows)

        log("✅", f"Tabel Screener ditemukan, {total_saham} saham di Screener [{screener_name}]", "LOG PADA MEMBACA DATA SCREENER YANG AKTIF")

        # Ambil screenshot screener setelah memastikan halaman siap
        await take_screenshot(page, screener_name)
        
        return screener_name, total_saham  # ✅ Perbaikan: Return screener_name & total saham

    except Exception as e:
        log("❌", f"Gagal memastikan halaman Screener siap: {e}", "LOG PADA MEMBACA DATA SCREENER YANG AKTIF")
        return None, 0  # ✅ Jika gagal, return None


# ============================
# ✅ SCREENSHOT SCREENER
# ============================
async def take_screenshot(page, screener_name):
    """Mengambil screenshot Screener setelah halaman terbuka sepenuhnya."""
    try:
        screener_element = page.locator("div.sc-6f84e760-3.gXCJki")
        await screener_element.wait_for(state="visible", timeout=5000)
        filename = f"{screener_name}-{datetime.datetime.now().strftime('%d%m%Y-%H%M%S')}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        await screener_element.screenshot(path=filepath)
        log("✅", f"Screenshot Screener: {filepath}", "LOG PADA MEMBACA DATA SCREENER YANG AKTIF")
    except Exception as e:
        log("❌", f"Gagal screenshot Screener: {e}", "LOG PADA MEMBACA DATA SCREENER YANG AKTIF")

# ============================
# ✅ HITUNG LOT SAHAM DENGAN 2 METODE
# ============================
async def calculate_lots(page, screener_name, method, value):
    """Menghitung jumlah lot berdasarkan metode 'Target-Amount' atau 'Jumlah-LOT'."""
    kategori_log = f"LOG PADA METODE {method.upper()} MEMNGHITUNG JUMLAH LOT DARI SCREENER [{screener_name}]"
    log("🚀", f"MEMNGHITUNG JUMLAH LOT, MEMBACA HARGA, KALKULASI HARGA [DATA SCREENER: {screener_name}]", kategori_log)

    # Cek kolom "Price"
    header_cells = await page.locator("thead tr th").all()
    headers = [await cell.inner_text() for cell in header_cells]

    if "Price" not in headers:
        log("❌", "Kolom 'Price' tidak ditemukan!", kategori_log)
        return []

    price_column_index = headers.index("Price") + 1
    rows = await page.locator("tbody tr:not([aria-hidden='true'])").all()
    saham_list = []

    for row in rows:
        symbol = await row.locator("td:first-child").text_content()
        price_text = await row.locator(f"td:nth-child({price_column_index})").text_content()

        if not price_text.strip():
            log("⚠️", f"Harga saham {symbol} kosong atau tidak valid! Skipping...", kategori_log)
            continue

        price = float(price_text.replace(',', '').strip())

        if method == "Target-Amount":
            lot = math.ceil(float(value) / price / 100)
            lot = max(lot, 1)  # Minimal 1 lot
        elif method == "Jumlah-LOT":
            lot = int(float(value))  # Konversi aman ke int
        else:
            log("❌", f"Metode {method} tidak dikenali saat menghitung lot.", kategori_log)
            continue

        total_investment = lot * price * 100
        log("✅", f"Berhasil menghitung Lot {symbol} | JUMLAH LOT = {lot} LOT | PRICE = {price:.2f} | TOTAL = {total_investment:,.0f}", kategori_log)
        saham_list.append({"symbol": symbol, "lot": lot})

    return saham_list


# ============================
# ✅ CEK TRADING AREA SEBELUM AUTO BUY
# ============================
async def check_trading_area(page):
    """Memeriksa apakah Trading Area tersedia sebelum proses Auto Buy."""
    try:
        log("🔍", "Memeriksa Trading Area...", "LOG CEK TRADING AREA SEBELUM AUTO BUY")

        # Cari elemen "Trading Area" di halaman
        trading_area_locator = page.locator("p:has-text('Trading Area')")

        # Cek apakah langsung terlihat
        if await trading_area_locator.is_visible():
            log("✅", "Trading Area ditemukan! Lanjut ke Auto Buy.", "LOG CEK TRADING AREA SEBELUM AUTO BUY")
            return True

        # Tunggu maksimal 3 detik
        await trading_area_locator.wait_for(state="visible", timeout=3000)
        log("✅", "Trading Area ditemukan! Lanjut ke Auto Buy.", "LOG CEK TRADING AREA SEBELUM AUTO BUY")
        return True

    except Exception:
        log("❌", "Trading Area tidak ditemukan! Menampilkan alert VBS dan menghentikan eksekusi.", "LOG CEK TRADING AREA SEBELUM AUTO BUY")
        
        # Tampilkan Alert VBS
        subprocess.run(["wscript", "D:\\wildan\\alert\\trading-area.vbs"])
        log("⚠️", "Alert VBS Trading Area telah ditampilkan. Program dihentikan.", "LOG CEK TRADING AREA SEBELUM AUTO BUY")
        
        return False


# ============================
# ✅ MENYIAPKAN HALAMAN PRODUK
# ============================
async def prepare_product_pages(context, saham_list):
    """Membuka dan memvalidasi halaman produk secara paralel."""
    log("🔄", "Menyiapkan halaman produk...", "MENYIAPKAN HALAMAN PRODUK")

    # Membuka semua halaman produk
    pages = [await context.new_page() for _ in saham_list]
    tasks = [page.goto(f"https://stockbit.com/symbol/{saham['symbol']}") for page, saham in zip(pages, saham_list)]
    await asyncio.gather(*tasks)

    log("✅", "Semua halaman produk telah dibuka!", "MENYIAPKAN HALAMAN PRODUK")

    # Mapping symbol ke page
    symbol_to_page = {saham['symbol']: page for saham, page in zip(saham_list, pages)}

    log("⏳", f"Menunggu halaman produk: {' | '.join([s['symbol'] for s in saham_list])}", "MENYIAPKAN HALAMAN PRODUK")

    valid_saham = []
    suspended_saham = []

    async def validate_page(page, saham):
        """Validasi halaman produk: apakah siap atau suspended."""
        try:
            await page.wait_for_load_state("load", timeout=3000)

            # Tunggu maksimal 3 detik untuk elemen Market tab muncul
            market_tab = page.locator("p.css-1ib0r0k.enwfma30", has_text="Market")
            await market_tab.first.wait_for(state="visible", timeout=3000)

            return saham  # ✅ Saham valid

        except Exception as e:
            suspended_saham.append(saham['symbol'])
            return None

    # Validasi semua halaman secara paralel
    validated_saham = await asyncio.gather(*(validate_page(symbol_to_page[s['symbol']], s) for s in saham_list))
    valid_saham = [s for s in validated_saham if s is not None]

    # Logging hasil validasi, hanya untuk saham yang disuspend
    if suspended_saham:
        log("🚫", f"{' | '.join(suspended_saham)} kemungkinan SUSPENDED! Di-skip otomatis.", "MENYIAPKAN HALAMAN PRODUK")

    # Tutup hanya halaman yang disuspend
    await close_suspended_pages(symbol_to_page, suspended_saham)

    log("✅", f"Total produk siap untuk Auto Buy: {len(valid_saham)} dari {len(saham_list)}", "MENYIAPKAN HALAMAN PRODUK")

    return pages, valid_saham, suspended_saham, symbol_to_page  # ✅ INI JANGAN HILANG


# ============================
# ✅ TUTUP HALAMAN DISUSPENDED
# ============================
async def close_suspended_pages(symbol_to_page: dict, suspended_saham: list):
    for symbol in suspended_saham:
        page = symbol_to_page.get(symbol)
        if not page:
            log("⚠️", f"Tidak ditemukan halaman untuk {symbol} saat ingin menutup.", "MENYIAPKAN HALAMAN PRODUK")
            continue

        try:
            await page.close()
            if not page.is_closed():
                log("❌", f"Gagal menutup halaman {symbol}.", "MENYIAPKAN HALAMAN PRODUK")
        except Exception as e:
            log("❌", f"Kesalahan saat menutup halaman {symbol}: {e}", "MENYIAPKAN HALAMAN PRODUK")

#============================
# SCREEN SHOOT HALAMAN ORDER
# ============================
async def screenshot_order_book(context, screener_name: str):
    page = await context.new_page()
    try:
        await page.goto("https://stockbit.com/securities/order")
        
        # Tunggu elemen Order Book muncul
        container = page.locator("div.sc-60165e0f-0.cRvzdT")
        await container.wait_for(state="visible", timeout=5000)
        
        filename = f"{screener_name}-order-{datetime.datetime.now().strftime('%d%m%Y-%H%M%S')}.png"
        filepath = os.path.join(ORDER_SCREENSHOT_DIR, filename)
        await container.screenshot(path=filepath)

        log("📸", f"Screenshot Orderbook: {filepath}", f"SCREEN SHOOT ORDERBOOK")
    except Exception as e:
        log("❌", f"Gagal screenshot Orderbook: {e}", f"SCREEN SHOOT ORDERBOOK")
        
        
# ============================
# ✅ AKTIFKAN TAB MARKET & PROSES HALAMAN PRODUK
# ============================
async def activate_market_and_scroll(pages, valid_saham, ready_saham, symbol_lot_mapping, screener_name):
    investment_logs = []
    screenshot_logs = []
    sukses_buy = []
    gagal_buy = []

    for page, saham in zip(pages, valid_saham):
        symbol = saham["symbol"]
        if symbol not in ready_saham:
            continue

        try:
            await page.bring_to_front()

            # Klik Tab Market
            market_button = page.locator("button[data-cy='button-filter-market']")
            await market_button.wait_for(state="visible", timeout=3000)
            await market_button.click()

            # Scroll 4 kali
            for _ in range(4):
                await page.keyboard.press("ArrowDown")
                await asyncio.sleep(0.1)

            # Input LOT
            lot = symbol_lot_mapping.get(symbol)
            input_lot = page.locator("input[data-cy='input-buy-lot']")
            await input_lot.fill(str(lot))
            await asyncio.sleep(0.3)

            # Cek apakah saldo tidak cukup
            insufficient = await page.locator("div.css-pxjiuh.eirfef012").is_visible(timeout=1000)

            if insufficient:
                # Ambil Investment dari elemen merah (karena saldo tidak cukup)
                investment_el = page.locator("p.investment-number.css-tjm1ey.enwfma30")
                investment_text = await investment_el.inner_text()

                # Ambil saldo dari daftar elemen Rp yang bukan label
                balance_els = await page.locator("p.css-1ib0r0k.enwfma30").all()
                saldo_text = ""
                for el in balance_els:
                    text = await el.inner_text()
                    if text.strip().startswith("Rp") and "Estimated" not in text:
                        saldo_text = text
                        break

                # Simpan log estimated investment meskipun gagal
                investment_logs.append(f"{symbol} | JUMLAH LOT = {lot} LOT | ESTIMATED INVESTMENT = {investment_text}")

                # Screenshot tetap diambil
                filename = f"{symbol}-{datetime.datetime.now().strftime('%d%m%Y-%H%M%S')}.png"
                filepath = os.path.join("D:/wildan/produk-screenshoot", filename)
                await page.screenshot(path=filepath)
                screenshot_logs.append(f"{symbol} ➜ Screenshot Produk: {filepath}")

                # Log gagal
                log("❌", f"Gagal BUY [{symbol}] {lot} Lot HARGA {investment_text} | Saldo {saldo_text} tidak cukup (Insufficient Trading Balance)",
                    f"HASIL AUTO BUY [MARKET ORDER] DARI [DATA SCREENER: {screener_name}]")
                gagal_buy.append(symbol)
                continue

            # Ambil estimated investment saat saldo cukup
            investment_el = page.locator("p.investment-number.css-58pbte.enwfma30")
            investment_text = await investment_el.inner_text()
            investment_logs.append(f"{symbol} | JUMLAH LOT = {lot} LOT | ESTIMATED INVESTMENT = {investment_text}")

            # Screenshot halaman produk
            filename = f"{symbol}-{datetime.datetime.now().strftime('%d%m%Y-%H%M%S')}.png"
            filepath = os.path.join("D:/wildan/produk-screenshoot", filename)
            await page.screenshot(path=filepath)
            screenshot_logs.append(f"{symbol} ➜ Screenshot Produk: {filepath}")

            # BUY SEQUENCE
            buy_button = page.locator("button[data-cy='button-buy']")
            await buy_button.click()

            confirm_button = page.locator("button:has-text('Confirm')")
            await confirm_button.wait_for(state="visible", timeout=3000)
            await confirm_button.click()

            return_button = page.locator("button:has-text('Return to Orderbook')")
            await return_button.wait_for(state="visible", timeout=5000)
            await return_button.click()

            sukses_buy.append(symbol)

        except Exception as e:
            gagal_buy.append(symbol)
            log("❌", f"Gagal memproses halaman produk {symbol}: {e}",
                f"HASIL AUTO BUY [MARKET ORDER] DARI [DATA SCREENER: {screener_name}]")

    # Log Investment dulu
    judul_investment = f"PERHITUNGAN ESTIMATED INVESTMENT [MARKET ORDER] DARI [DATA SCREENER: {screener_name}]"
    log(None, judul_investment, judul_investment)
    for text in investment_logs:
        log("📊", text, judul_investment)

    # Lalu log hasil auto buy
    judul_hasil = f"HASIL AUTO BUY [MARKET ORDER] DARI [DATA SCREENER: {screener_name}]"
    log(None, judul_hasil, judul_hasil)
    if sukses_buy:
        log("✅", f"Sukses Membeli : {' | '.join(sukses_buy)}", judul_hasil)
    if gagal_buy:
        log("❌", f"Gagal Buy : {' | '.join(gagal_buy)}", judul_hasil)

    # Terakhir log screenshot
    judul_screenshot = f"SCREEN SHOOT HALAMAN PRODUK DARI [DATA SCREENER: {screener_name}]"
    log(None, judul_screenshot, judul_screenshot)
    for text in screenshot_logs:
        log("📸", text, judul_screenshot)




# ============================
# 🚀 EKSEKUSI UTAMA
# ============================
async def run():
    start_time = time.time()

    # ===============================
    # LOG CONFIG JSON (Method, Value)
    # ===============================
    CONFIG_PATH = "D:/wildan/config-json/config.json"
    method = "-"
    value = "-"
    exec_time = "-"

    try:
        with open(CONFIG_PATH, "r") as f:
            config_data = json.load(f)
            method = config_data.get("method")
            value = config_data.get("value")
            exec_time = config_data.get("execution_time")

            # Validasi method dan value wajib ada
            if not method or not value:
                log("❌", "Konfigurasi method/value tidak valid di config.json. Program dihentikan.", "LOG CONFIGURASI")
                return

            # ✅ Log konfigurasi
            log(None, "LOG CONFIGURASI", "LOG CONFIGURASI")
            log("📦", f"File Configurasi\t: {CONFIG_PATH}", "LOG CONFIGURASI")
            log("✅", f"Metode\t\t\t: {method}", "LOG CONFIGURASI")
            log("🎯", f"Value \t\t\t: {value}", "LOG CONFIGURASI")

    except Exception as e:
        log("❌", f"Gagal membaca config.json: {e}", "LOG CONFIGURASI")
        log("⚠️", "Program dihentikan karena tidak bisa membaca konfigurasi", "LOG CONFIGURASI")
        return

    # ✅ Lanjut proses Playwright
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CHROME_DEBUGGER_URL)
        context = browser.contexts[0]

        log("🚀", "Membuka Stockbit Screener...", "LOG PADA MEMBACA DATA SCREENER YANG AKTIF")
        page = await context.new_page()
        await page.goto(STOCKBIT_URL)

        if page.url.startswith(LOGIN_URL):
            log("⚠️", "User belum login! Menampilkan popup peringatan.", "LOG PADA MEMBACA DATA SCREENER YANG AKTIF")
            subprocess.run(["wscript", VBS_ALERT_PATH])
            log("❌", "Proses dihentikan. Silakan login terlebih dahulu.", "LOG PADA MEMBACA DATA SCREENER YANG AKTIF")
            return

        screener_name, total_saham = await ensure_screener_ready(page)
        if not screener_name or total_saham == 0:
            log("❌", "Gagal mendapatkan data saham dari Screener! Eksekusi dihentikan.", "LOG PADA MEMBACA DATA SCREENER YANG AKTIF")
            return

        saham_list = await calculate_lots(page, screener_name, method, value)
        if not saham_list:
            log("❌", "Tidak ada saham yang valid untuk dibeli. Proses dihentikan.", f"LOG PADA MEMNGHITUNG JUMLAH LOT DARI SCREENER [{screener_name}]")
            return

        if not await check_trading_area(page):
            log("❌", "Trading Area tidak tersedia. Program dihentikan.", "LOG CEK TRADING AREA SEBELUM AUTO BUY")
            return
        log("✅", "Trading Area tersedia. Siap lanjut ke Auto Buy.", "LOG CEK TRADING AREA SEBELUM AUTO BUY")

        pages, valid_saham, suspended_saham, symbol_to_page = await prepare_product_pages(context, saham_list)
        if not valid_saham:
            log("❌", "Tidak ada saham yang valid setelah validasi halaman produk. Proses dihentikan.", "MENYIAPKAN HALAMAN PRODUK")
            return

        ready_saham = [s['symbol'] for s in valid_saham if s['symbol'] not in suspended_saham]
        pages_filtered = [symbol_to_page[s['symbol']] for s in valid_saham]
        symbol_lot_mapping = {s['symbol']: s['lot'] for s in saham_list}

        await activate_market_and_scroll(pages_filtered, valid_saham, ready_saham, symbol_lot_mapping, screener_name)
        await screenshot_order_book(context, screener_name)

        execution_time = round(time.time() - start_time, 2)
        log("✅", f"Proses selesai! Total waktu eksekusi: {execution_time} detik", "TOTAL EKSEKUSI")



if __name__ == "__main__":
    asyncio.run(run())
