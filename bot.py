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
from urllib.parse import urlparse, parse_qs, unquote
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

COUNTRY_FLAGS = {
    "United States": "🇺🇸", "Germany": "🇩🇪", "Netherlands": "🇳🇱",
    "France": "🇫🇷", "United Kingdom": "🇬🇧", "Canada": "🇨🇦",
    "Singapore": "🇸🇬", "Japan": "🇯🇵", "Russia": "🇷🇺",
    "Ukraine": "🇺🇦", "Finland": "🇫🇮", "Sweden": "🇸🇪",
    "Poland": "🇵🇱", "Turkey": "🇹🇷", "Iran": "🇮🇷",
    "China": "🇨🇳", "South Korea": "🇰🇷", "Brazil": "🇧🇷",
    "India": "🇮🇳", "Australia": "🇦🇺", "Switzerland": "🇨🇭",
    "Austria": "🇦🇹", "Czech Republic": "🇨🇿", "Romania": "🇷🇴",
    "Hungary": "🇭🇺", "Bulgaria": "🇧🇬", "Latvia": "🇱🇻",
    "Lithuania": "🇱🇹", "Estonia": "🇪🇪", "Moldova": "🇲🇩",
    "Luxembourg": "🇱🇺", "Belgium": "🇧🇪", "Italy": "🇮🇹",
    "Spain": "🇪🇸", "Portugal": "🇵🇹", "Norway": "🇳🇴",
    "Denmark": "🇩🇰", "Iceland": "🇮🇸", "Israel": "🇮🇱",
    "UAE": "🇦🇪", "Saudi Arabia": "🇸🇦", "Mexico": "🇲🇽",
    "Argentina": "🇦🇷", "Chile": "🇨🇱", "Colombia": "🇨🇴",
}

_geo_cache = {}


# ─── پیدا کردن لوکیشن IP ───────────────────────────────
def get_location(host):
    # اگر hostname باشه نه IP، برگردون unknown
    if not host.replace('.', '').isdigit():
        return {"country": "Unknown", "city": "", "isp": "", "flag": "🌍"}

    if host in _geo_cache:
        return _geo_cache[host]

    try:
        response = requests.get(
            f"http://ip-api.com/json/{host}?fields=country,city,isp",
            timeout=5
        )
        data = response.json()
        if data.get('country'):
            country = data.get('country', 'Unknown')
            city = data.get('city', '')
            isp = data.get('isp', '')
            flag = COUNTRY_FLAGS.get(country, '🌍')
            result = {"country": country, "city": city, "isp": isp, "flag": flag}
            _geo_cache[host] = result
            return result
    except Exception:
        pass

    result = {"country": "Unknown", "city": "", "isp": "", "flag": "🌍"}
    _geo_cache[host] = result
    return result


# ─── پارس کردن لینک پروکسی (هر دو فرمت) ───────────────
def parse_proxy_link(line):
    """
    پشتیبانی از هر دو فرمت:
    - https://t.me/proxy?server=...&port=...&secret=...
    - tg://proxy?server=...&port=...&secret=...
    """
    line = line.strip()

    if not line:
        return None

    # تبدیل t.me به tg://
    if line.startswith("https://t.me/proxy") or line.startswith("http://t.me/proxy"):
        tg_link = line.replace("https://t.me/proxy", "tg://proxy", 1)
        tg_link = tg_link.replace("http://t.me/proxy", "tg://proxy", 1)
    elif line.startswith("tg://proxy"):
        tg_link = line
    else:
        return None

    try:
        parsed = urlparse(tg_link)
        params = parse_qs(parsed.query)
        host = params.get('server', [''])[0]
        port = params.get('port', [''])[0]
        secret = params.get('secret', [''])[0]

        if not host or not port:
            return None

        return {
            "link": tg_link,
            "host": host,
            "port": port,
            "secret": secret,
            "name": "",
            "country": "",
            "city": "",
            "isp": "",
            "flag": "🌍",
        }
    except Exception:
        return None


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
        if not app_div or 'data-page' not in app_div.attrs:
            print("❌ div#app یا data-page پیدا نشد")
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
                    "port": str(p.get('port', '')),
                    "secret": p.get('secret', ''),
                    "name": p.get('name', ''),
                    "country": "",
                    "city": "",
                    "isp": "",
                    "flag": "🌍",
                })
        return result

    except Exception as e:
        print(f"❌ خطا ProxyBolt: {e}")
        return []


# ─── دریافت از فایل‌های متنی GitHub ────────────────────
def get_from_text_files():
    all_proxies = []
    for url in PROXY_SOURCES['text_files']:
        try:
            response = requests.get(url, headers=HEADERS, timeout=8)
            response.raise_for_status()
            lines = response.text.strip().split('\n')
            count = 0
            for line in lines:
                proxy = parse_proxy_link(line)
                if proxy:
                    all_proxies.append(proxy)
                    count += 1
            if count > 0:
                file_num = url.split('no')[-1].replace('.txt', '')
                print(f"  📄 فایل {file_num}: {count} پروکسی")
        except Exception as e:
            print(f"  ⚠️ خطا در فایل: {e}")
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


# ─── دریافت لوکیشن ─────────────────────────────────────
def enrich_with_location(proxies):
    print(f"🗺 در حال دریافت لوکیشن {len(proxies)} پروکسی...")
    for p in proxies:
        geo = get_location(p['host'])
        p['country'] = geo['country']
        p['city'] = geo['city']
        p['isp'] = geo['isp']
        p['flag'] = geo['flag']
        time.sleep(0.2)
    return proxies


# ─── دریافت + فیلتر پروکسی‌های فعال ───────────────────
def get_active_proxies(max_check=80, return_count=5):
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

    to_check = unique[:max_check]
    print(f"🔍 در حال چک اتصال {len(to_check)} پروکسی...")

    with ThreadPoolExecutor(max_workers=40) as executor:
        results = list(executor.map(check_proxy, to_check))
    active = [r for r in results if r is not None]

    print(f"✅ فعال: {len(active)} پروکسی")

    random.shuffle(active)
    active = active[:return_count]

    active = enrich_with_location(active)
    return active


# ─── فرمت پیام ─────────────────────────────────────────
def escape_md(text):
    """Escape کردن کاراکترهای خاص MarkdownV2"""
    special = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for ch in special:
        text = text.replace(ch, f'\\{ch}')
    return text


def format_message(proxies):
    lines = [
        "🔐 *پروکسی‌های تلگرام \\- فعال و تست شده*",
        "━━━━━━━━━━━━━━━━━━━━\n"
    ]

    for i, p in enumerate(proxies, 1):
        flag = p.get('flag', '🌍')
        country = escape_md(p.get('country', 'Unknown'))
        city = escape_md(p.get('city', ''))
        isp = escape_md(p.get('isp', ''))
        host = escape_md(p.get('host', ''))
        port = escape_md(str(p.get('port', '')))
        link = p.get('link', '')

        location_str = f"{city}, {country}" if city else country

        lines.append(f"*{i}\\. {flag} {location_str}*")
        lines.append(f"🖥 `{p.get('host')}:{p.get('port')}`")
        if isp:
            lines.append(f"🏢 {isp}")
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
    proxies = get_active_proxies(max_check=80, return_count=5)

    if proxies:
        msg = format_message(proxies)
        await send_to_channel(msg)
    else:
        print("⚠️ هیچ پروکسی فعالی پیدا نشد!")


async def main():
    print("🚀 ربات پروکسی شروع به کار کرد!")

    await job()

    def run_job():
        asyncio.create_task(job())

    schedule.every(5).minutes.do(run_job)

    while True:
        schedule.run_pending()
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
