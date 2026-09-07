import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

URL = "https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

CHAT_IDS = [
    os.environ["TELEGRAM_CHAT_ID"],
    os.environ["TELEGRAM_CHAT_ID_2"]
]

STATE_FILE = "state.json"
UK_TZ = ZoneInfo("Europe/London")


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

    for chat_id in CHAT_IDS:
        try:
            response = requests.post(
                telegram_url,
                data={
                    "chat_id": chat_id,
                    "text": message
                },
                timeout=30
            )

            response.raise_for_status()
            print(f"Telegram message sent successfully to {chat_id}")

        except Exception as e:
            print(f"Telegram error for {chat_id}: {e}")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as file:
            return json.load(file)

    return {
        "previous_status": "UNKNOWN",
        "last_open_message": "",
        "last_morning_message": "",
        "last_night_message": ""
    }


def save_state(state):
    with open(STATE_FILE, "w") as file:
        json.dump(state, file, indent=2)


# --------------------------------------------------
# TEST MESSAGE
# --------------------------------------------------

if os.environ.get("TEST_MESSAGE") == "true":

    message = """🧪🇦🇺 AUSTRALIA 462 TEST MESSAGE

Your Peru visa checker is working.

This test message was sent to all configured Telegram accounts.

The system will:
🔎 Check every 5 minutes
🚨 Alert immediately if Peru opens
⏰ Send updates every 30 minutes while OPEN
🌅 Send a morning status
🌙 Send a night status

Current status will be checked normally after this test."""

    send_telegram(message)

    print("🧪 TEST MESSAGE SENT!")
    exit()


# --------------------------------------------------
# NORMAL CHECK
# --------------------------------------------------

now = datetime.now(UK_TZ)
today = now.strftime("%Y-%m-%d")

state = load_state()
status = get_peru_status()

print(f"🇦🇺 Peru status: {status}")
print(f"🇬🇧 UK time: {now}")
print(f"Previous status: {state['previous_status']}")


# --------------------------------------------------
# IMMEDIATE OPEN ALERT
# --------------------------------------------------

if status == "OPEN" and state["previous_status"] != "OPEN":

    message = """🚨🇦🇺 AUSTRALIA 462 VISA IS OPEN! 🇵🇪

Peru's Work and Holiday (subclass 462) cap is now OPEN.

APPLY NOW!

Official Home Affairs page:
https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"""

    send_telegram(message)

    state["last_open_message"] = now.isoformat()

    print("🚨 OPEN ALERT SENT!")


# --------------------------------------------------
# EVERY 30 MINUTES WHILE OPEN
# --------------------------------------------------

elif status == "OPEN":

    last_message = state.get("last_open_message", "")
    should_send = False

    if not last_message:
        should_send = True
    else:
        try:
            last_time = datetime.fromisoformat(last_message)

            if now - last_time >= timedelta(minutes=30):
                should_send = True

        except Exception:
            should_send = True

    if should_send:

        message = """🚨🇦🇺 AUSTRALIA 462 UPDATE

Peru's Work and Holiday (subclass 462) cap is STILL OPEN! 🇵🇪

Check the official Home Affairs website and apply as soon as possible."""

        send_telegram(message)

        state["last_open_message"] = now.isoformat()

        print("⏰ 30-MINUTE OPEN UPDATE SENT!")


# --------------------------------------------------
# MORNING MESSAGE — 08:00 UK
# --------------------------------------------------

if now.hour == 8 and now.minute < 10:

    if state.get("last_morning_message") != today:

        if status == "OPEN":
            status_text = "🚨 OPEN — Peru's cap is currently OPEN!"
        elif status == "PAUSED":
            status_text = "⏸️ PAUSED — Peru's cap is currently PAUSED."
        else:
            status_text = f"Current status: {status}"

        message = f"""🌅🇦🇺 AUSTRALIA 462 MORNING UPDATE

Date: {today}

🇵🇪 Peru status:
{status_text}

The checker is monitoring every 5 minutes."""

        send_telegram(message)

        state["last_morning_message"] = today

        print("🌅 MORNING MESSAGE SENT!")


# --------------------------------------------------
# NIGHT MESSAGE — 23:00 UK
# --------------------------------------------------

if now.hour == 23 and now.minute < 10:

    if state.get("last_night_message") != today:

        if status == "OPEN":
            status_text = "🚨 OPEN — Peru's cap is currently OPEN!"
        elif status == "PAUSED":
            status_text = "⏸️ PAUSED — Peru's cap is currently PAUSED."
        else:
            status_text = f"Current status: {status}"

        message = f"""🌙🇦🇺 AUSTRALIA 462 NIGHT UPDATE

Date: {today}

🇵🇪 Peru status:
{status_text}

The checker will continue monitoring overnight every 5 minutes."""

        send_telegram(message)

        state["last_night_message"] = today

        print("🌙 NIGHT MESSAGE SENT!")


state["previous_status"] = status
save_state(state)

print("✅ Check completed.")
