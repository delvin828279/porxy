import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
import schedule
import time
import threading
import os

# ─── تنظیمات ───────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")  # مثال: @myproxychannel
PROXY_URL = "https://proxybolt.link/"
# ───────────────────────────────────────────────────────

def get_proxies():
    """دریافت پروکسی‌ها از سایت"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(PROXY_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        proxies = []
        
        # جستجو در تگ‌های مختلف
        # تلاش برای یافتن جدول پروکسی
        table = soup.find("table")
        if table:
            rows = table.find_all("tr")[1:]  # skip header
            for row in rows[:10]:  # فقط ۱۰ پروکسی اول
                cols = row.find_all("td")
                if len(cols) >= 2:
                    ip = cols[0].get_text(strip=True)
                    port = cols[1].get_text(strip=True)
                    ptype = cols[2].get_text(strip=True) if len(cols) > 2 else "HTTP"
                    country = cols[3].get_text(strip=True) if len(cols) > 3 else "?"
                    if ip and port:
                        proxies.append({
                            "ip": ip,
                            "port": port,
                            "type": ptype,
                            "country": country
                        })
        
        # اگر جدول نبود، از textarea یا pre بخوان
        if not proxies:
            pre = soup.find("pre") or soup.find("textarea")
            if pre:
                lines = pre.get_text().strip().split("\n")
                for line in lines[:10]:
                    line = line.strip()
                    if ":" in line:
                        parts = line.split(":")
                        proxies.append({
                            "ip": parts[0],
                            "port": parts[1] if len(parts) > 1 else "?",
                            "type": "HTTP",
                            "country": "?"
                        })
        
        return proxies
    
    except Exception as e:
        print(f"❌ خطا در دریافت پروکسی: {e}")
        return []


def format_message(proxies):
    """فرمت‌بندی پیام برای تلگرام"""
    if not proxies:
        return None
    
    msg = "🌐 *پروکسی‌های جدید*\n"
    msg += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for p in proxies:
        flag = "🏳️"
        msg += f"🔹 `{p['ip']}:{p['port']}`\n"
        msg += f"   📡 نوع: `{p['type']}` | {p['country']}\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += f"🕐 بروزرسانی هر ۵ دقیقه\n"
    msg += f"🔗 منبع: [ProxyBolt](https://proxybolt.link/)"
    
    return msg


async def send_to_channel(message):
    """ارسال پیام به کانال"""
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        print("✅ پروکسی‌ها با موفقیت ارسال شدند")
    except Exception as e:
        print(f"❌ خطا در ارسال پیام: {e}")


def job():
    """کار اصلی: دریافت و ارسال پروکسی"""
    print("🔄 در حال دریافت پروکسی...")
    proxies = get_proxies()
    
    if proxies:
        message = format_message(proxies)
        if message:
            asyncio.run(send_to_channel(message))
    else:
        print("⚠️ پروکسی‌ای پیدا نشد")


def run_scheduler():
    """اجرای زمان‌بند"""
    schedule.every(5).minutes.do(job)
    
    print("🚀 ربات شروع به کار کرد!")
    print("⏰ هر ۵ دقیقه پروکسی ارسال می‌شود")
    
    # اجرای فوری اول
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":
    run_scheduler()
