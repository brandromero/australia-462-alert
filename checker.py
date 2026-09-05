import requests
from bs4 import BeautifulSoup
import os

URL = "https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

STATUS_FILE = "status.txt"


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
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )


def get_previous_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as file:
            return file.read().strip()

    return "UNKNOWN"


def save_status(status):
    with open(STATUS_FILE, "w") as file:
        file.write(status)


print("🇦🇺 Australia 462 Peru checker started.")

try:
    status = get_peru_status()
    previous_status = get_previous_status()

    print(f"Peru status: {status}")
    print(f"Previous status: {previous_status}")

    if status == "OPEN" and previous_status != "OPEN":

        message = """🚨🇦🇺 AUSTRALIA 462 VISA IS OPEN! 🇵🇪

Peru's Work and Holiday (subclass 462) cap is now OPEN.

APPLY NOW!

Official Home Affairs page:
https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"""

        send_telegram(message)

        print("🚨 ALERT SENT!")

    save_status(status)

except Exception as e:
    print(f"Error: {e}")
    raise
