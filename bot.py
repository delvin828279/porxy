import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
import schedule
import time
import os
import re

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")
PROXY_URL = "https://proxybolt.link/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

def get_proxies():
    try:
        session = requests.Session()
        response = session.get(PROXY_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()

        print(f"📄 Status: {response.status_code}")
        print(f"📄 محتوا (500 کاراکتر اول):\n{response.text[:500]}\n")

        soup = BeautifulSoup(response.text, "html.parser")
        proxies = []

        # روش ۱: جدول
        table = soup.find("table")
        if table:
            rows = table.find_all("tr")[1:]
            print(f"✅ جدول پیدا شد - {len(rows)} ردیف")
            for row in rows[:5]:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    ip = cols[0].get_text(strip=True)
                    port = cols[1].get_text(strip=True)
                    ptype = cols[2].get_text(strip=True) if len(cols) > 2 else "HTTP"
                    country = cols[3].get_text(strip=True) if len(cols) > 3 else "🌍"
                    if re.match(r'\d+\.\d+\.\d+\.\d+', ip):
                        proxies.append({"ip": ip, "port": port, "type": ptype, "country": country})

        # روش ۲: متن آزاد با regex
        if not proxies:
            print("🔍 جستجو با Regex...")
            pattern = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})', response.text)
            for ip, port in pattern[:5]:
                proxies.append({"ip": ip, "port": port, "type": "HTTP", "country": "🌍"})
            print(f"✅ Regex: {len(proxies)} پروکسی")

        # روش ۳: pre یا code tag
        if not proxies:
            for tag in soup.find_all(["pre", "code", "textarea", "p"]):
                text = tag.get_text()
                found = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})', text)
                for ip, port in found:
                    proxies.append({"ip": ip, "port": port, "type": "HTTP", "country": "🌍"})
                if proxies:
                    break

        print(f"📊 نتیجه: {len(proxies)} پروکسی پیدا شد")
        return proxies

    except Exception as e:
        print(f"❌ خطا: {e}")
        return []


def format_message(proxies):
    if not proxies:
        return None

    lines = ["🌐 *پروکسی‌های رایگان*", "━━━━━━━━━━━━━━━━━━\n"]
    for p in proxies:
        lines.append(f"🔹 `{p['ip']}:{p['port']}`")
        lines.append(f"   📡 `{p['type']}` | {p['country']}\n")

    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("⏱ بروزرسانی هر ۵ دقیقه")
    lines.append("🔗 [ProxyBolt](https://proxybolt.link/)")

    return "\n".join(lines)


async def send_to_channel(message):
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        print("✅ پیام ارسال شد!")
    except Exception as e:
        print(f"❌ خطا در ارسال: {e}")


def job():
    print("\n" + "="*40)
    print("🔄 شروع دریافت پروکسی...")
    proxies = get_proxies()

    if proxies:
        msg = format_message(proxies)
        asyncio.run(send_to_channel(msg))
    else:
        print("⚠️ هیچ پروکسی پیدا نشد - ساختار سایت رو بررسی کن")


def main():
    print("🚀 ربات شروع به کار کرد!")
    job()  # اجرای فوری

    schedule.every(5).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":
    main()
