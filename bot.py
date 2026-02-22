import requests
from bs4 import BeautifulSoup
import json
import random
import socket
import os
import asyncio
import schedule
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs
from telegram import Bot

# ─── تنظیمات ───────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")

PROXY_SOURCES = {
    'proxybolt': 'https://proxybolt.link/',
    'text_files': [
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no1.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no2.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no3.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no4.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no5.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no6.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no7.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no8.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no9.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no10.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no11.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no12.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no13.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no14.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no15.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no16.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no17.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no18.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no19.txt",
        "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/refs/heads/main/telegram_proxy_no20.txt",
    ]
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

# ─── دریافت از ProxyBolt ────────────────────────────────
def get_from_proxybolt():
    try:
        response = requests.get(
            PROXY_SOURCES['proxybolt'],
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        app_div = soup.find('div', id='app')
        if not app_div:
            print("❌ div#app پیدا نشد")
            return []

        if 'data-page' not in app_div.attrs:
            print("❌ data-page پیدا نشد")
            return []

        page_data = json.loads(app_div['data-page'])
        proxies_data = page_data.get('props', {}).get('proxies', [])

        print(f"✅ ProxyBolt: {len(proxies_data)} پروکسی پیدا شد")

        result = []
        for p in proxies_data:
            if p.get('host'):
                link = f"tg://proxy?server={p.get('host')}&port={p.get('port')}&secret={p.get('secret')}"
                result.append({
                    "link": link,
                    "host": p.get('host'),
                    "port": p.get('port'),
                    "name": p.get('name', ''),
                    "country": p.get('country', '🌍'),
                })
        return result

    except Exception as e:
        print(f"❌ خطا ProxyBolt: {e}")
        return []


# ─── دریافت از فایل‌های متنی ────────────────────────────
def get_from_text_files():
    all_proxies = []
    for url in PROXY_SOURCES['text_files']:
        try:
            response = requests.get(url, headers=HEADERS, timeout=8)
            response.raise_for_status()
            lines = response.text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('tg://proxy'):
                    parsed = urlparse(line)
                    params = parse_qs(parsed.query)
                    host = params.get('server', [''])[0]
                    port = params.get('port', [''])[0]
                    if host:
                        all_proxies.append({
                            "link": line,
                            "host": host,
                            "port": port,
                            "name": "",
                            "country": "🌍",
                        })
        except Exception:
            continue

    print(f"✅ فایل‌های متنی: {len(all_proxies)} پروکسی")
    return all_proxies


# ─── چک کردن اتصال ─────────────────────────────────────
def check_proxy(proxy):
    try:
        host = proxy['host']
        port = int(proxy['port'])
        with socket.create_connection((host, port), timeout=2):
            return proxy
    except Exception:
        return None


# ─── دریافت + فیلتر پروکسی‌های فعال ───────────────────
def get_active_proxies(max_check=60, return_count=5):
    bolt = get_from_proxybolt()
    files = get_from_text_files()
    all_proxies = bolt + files

    # حذف تکراری
    seen = set()
    unique = []
    for p in all_proxies:
        key = f"{p['host']}:{p['port']}"
        if key not in seen:
            seen.add(key)
            unique.append(p)

    print(f"📊 کل منحصربفرد: {len(unique)}")

    # چک اتصال
    to_check = unique[:max_check]
    print(f"🔍 در حال چک {len(to_check)} پروکسی...")

    active = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(check_proxy, to_check))
    active = [r for r in results if r is not None]

    random.shuffle(active)
    print(f"✅ فعال: {len(active)} پروکسی")
    return active[:return_count]


# ─── فرمت پیام ─────────────────────────────────────────
def format_message(proxies):
    lines = [
        "🔐 *پروکسی‌های تلگرام \- فعال و تست شده*",
        "━━━━━━━━━━━━━━━━━━━━\n"
    ]

    for i, p in enumerate(proxies, 1):
        name = p.get('name', '') or f"Proxy {i}"
        country = p.get('country', '🌍')
        host = p.get('host', '')
        port = p.get('port', '')
        link = p.get('link', '')

        lines.append(f"*{i}\\. {name}* {country}")
        lines.append(f"🖥 `{host}:{port}`")
        lines.append(f"[🔗 اتصال مستقیم به تلگرام]({link})\n")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("⏱ بروزرسانی هر ۵ دقیقه")
    lines.append("✅ همه پروکسی‌ها تست شده و فعال هستن")

    return "\n".join(lines)


# ─── ارسال به کانال ─────────────────────────────────────
async def send_to_channel(message):
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True
        )
        print("✅ پیام ارسال شد!")
    except Exception as e:
        print(f"❌ خطا در ارسال: {e}")


# ─── کار اصلی ───────────────────────────────────────────
async def job():
    print("\n" + "="*45)
    print("🔄 شروع دریافت پروکسی...")
    proxies = get_active_proxies(max_check=60, return_count=5)

    if proxies:
        msg = format_message(proxies)
        await send_to_channel(msg)
    else:
        print("⚠️ هیچ پروکسی فعالی پیدا نشد!")


async def main():
    print("🚀 ربات پروکسی شروع به کار کرد!")

    await job()  # اجرای فوری اول

    def run_job():
        asyncio.create_task(job())

    schedule.every(5).minutes.do(run_job)

    while True:
        schedule.run_pending()
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
