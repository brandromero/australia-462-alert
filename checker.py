import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

STATE_FILE = "state.json"


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

    response = requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )

    response.raise_for_status()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as file:
            return json.load(file)

    return {
        "initialized": False,
        "previous_status": "UNKNOWN",
        "last_daily_message": ""
    }


def save_state(state):
    with open(STATE_FILE, "w") as file:
        json.dump(state, file, indent=2)


# UK time
now = datetime.now(ZoneInfo("Europe/London"))
today = now.strftime("%Y-%m-%d")

state = load_state()
status = get_peru_status()

print(f"🇦🇺 Peru status: {status}")
print(f"🇬🇧 UK time: {now}")
print(f"Previous status: {state['previous_status']}")


# --------------------------------------------------
# FIRST RUN MESSAGE
# --------------------------------------------------

if not state["initialized"]:

    message = f"""🇦🇺🇵🇪 AUSTRALIA 462 CHECKER IS WORKING! ✅

This is the first automatic check.

Current Peru status: {status}

The checker will now continue monitoring every 5 minutes, 24/7.

You will receive:
🚨 An immediate alert if Peru opens
🌙 A daily status message at the end of the day"""

    send_telegram(message)

    state["initialized"] = True

    print("📩 First-run test message sent.")


# --------------------------------------------------
# OPEN ALERT
# --------------------------------------------------

if status == "OPEN" and state["previous_status"] != "OPEN":

    message = """🚨🇦🇺 AUSTRALIA 462 VISA IS OPEN! 🇵🇪

Peru's Work and Holiday (subclass 462) cap is now OPEN.

APPLY NOW!

Official Home Affairs page:
https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"""

    send_telegram(message)

    print("🚨 OPEN ALERT SENT!")


# --------------------------------------------------
# DAILY MESSAGE
# Around 23:55 UK time
# --------------------------------------------------

if now.hour == 23 and now.minute >= 55:

    if state["last_daily_message"] != today:

        if status == "OPEN":
            message = f"""🌙🇦🇺 DAILY AUSTRALIA 462 UPDATE

Date: {today}

🚨 PERU IS CURRENTLY OPEN! 🇵🇪

If you haven't applied yet, check the official Home Affairs website now."""

        else:
            message = f"""🌙🇦🇺 DAILY AUSTRALIA 462 UPDATE

Date: {today}

Peru did not open today.

Current status: {status}

🔄 The checker will continue monitoring every 5 minutes, 24/7."""

        send_telegram(message)

        state["last_daily_message"] = today

        print("📩 Daily message sent.")


state["previous_status"] = status
save_state(state)

print("✅ Check completed.")
