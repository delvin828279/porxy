import asyncio
import os
import schedule
import time
from playwright.async_api import async_playwright
from telegram import Bot
import re

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")

async def get_proxies_playwright():
    proxies = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            page = await browser.new_page()

            print("🌐 در حال باز کردن سایت...")
            await page.goto("https://proxybolt.link/", timeout=30000)

            # صبر کن تا JavaScript لود بشه
            await page.wait_for_timeout(5000)

            content = await page.content()
            print(f"📄 سایز محتوا: {len(content)} کاراکتر")

            # روش ۱: جدول
            rows = await page.query_selector_all("table tr")
            print(f"🔍 تعداد ردیف جدول: {len(rows)}")

            for row in rows[1:6]:  # skip header, max 5
                cols = await row.query_selector_all("td")
                if len(cols) >= 2:
                    ip = await cols[0].inner_text()
                    port = await cols[1].inner_text()
                    ptype = await cols[2].inner_text() if len(cols) > 2 else "HTTP"
                    country = await cols[3].inner_text() if len(cols) > 3 else "🌍"
                    ip = ip.strip()
                    port = port.strip()
                    if re.match(r'\d+\.\d+\.\d+\.\d+', ip):
                        proxies.append({
                            "ip": ip,
                            "port": port,
                            "type": ptype.strip(),
                            "country": country.strip()
                        })

            # روش ۲: Regex روی محتوای کامل
            if not proxies:
                print("🔍 جستجو با Regex در محتوای کامل...")
                found = re.findall(
                    r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[:\s]+(\d{2,5})',
                    content
                )
                for ip, port in found[:5]:
                    proxies.append({
                        "ip": ip,
                        "port": port,
                        "type": "HTTP",
                        "country": "🌍"
                    })

            await browser.close()
            print(f"✅ {len(proxies)} پروکسی پیدا شد")

    except Exception as e:
        print(f"❌ خطا در Playwright: {e}")

    return proxies


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


def format_message(proxies):
    lines = ["🌐 *پروکسی‌های رایگان*", "━━━━━━━━━━━━━━━━━━\n"]
    for p in proxies:
        lines.append(f"🔹 `{p['ip']}:{p['port']}`")
        lines.append(f"   📡 `{p['type']}` | {p['country']}\n")
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("⏱ بروزرسانی هر ۵ دقیقه")
    lines.append("🔗 [ProxyBolt](https://proxybolt.link/)")
    return "\n".join(lines)


async def job():
    print("\n" + "="*40)
    print("🔄 شروع دریافت پروکسی...")
    proxies = await get_proxies_playwright()
    if proxies:
        msg = format_message(proxies)
        await send_to_channel(msg)
    else:
        print("⚠️ پروکسی پیدا نشد!")


async def main():
    print("🚀 ربات شروع به کار کرد!")

    # نصب مرورگر
    import subprocess
    subprocess.run(["playwright", "install", "chromium"], check=True)
    subprocess.run(["playwright", "install-deps", "chromium"], check=True)

    await job()  # اجرای فوری

    while True:
        schedule.every(5).minutes.do(lambda: asyncio.create_task(job()))
        schedule.run_pending()
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
