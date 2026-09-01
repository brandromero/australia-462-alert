import requests
from bs4 import BeautifulSoup
import time
import os

URL = "https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CHECK_INTERVAL = 5 * 60  # 5 minutes


def get_peru_status():
    response = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(" ", strip=True)

    peru = text.lower().find("peru")

    if peru == -1:
        return "UNKNOWN"

    section = text[peru:peru + 150].lower()

    if "paused" in section:
        return "PAUSED"

    if "open" in section:
        return "OPEN"

    if "closed" in section:
        return "CLOSED"

    return "UNKNOWN"


def send_telegram(message):
    telegram_url = (
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    )

    requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )


print("🇦🇺 Australia 462 Peru checker started.")

while True:

    try:
        status = get_peru_status()

        print(f"Peru status: {status}")

        if status == "OPEN":

            message = """🚨🇦🇺 AUSTRALIA 462 VISA IS OPEN! 🇵🇪

Peru's Work and Holiday (subclass 462) cap is now OPEN.

APPLY NOW!

Official Home Affairs page:
https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"""

            send_telegram(message)

            print("🚨 ALERT SENT!")
            break

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(CHECK_INTERVAL)
