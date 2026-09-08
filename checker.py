import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo


URL = "https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

CHAT_IDS = [
    os.environ["TELEGRAM_CHAT_ID"],
    os.environ["TELEGRAM_CHAT_ID_2"]
]

STATE_FILE = "state.json"

UK_TZ = ZoneInfo("Europe/London")


# --------------------------------------------------
# TELEGRAM
# --------------------------------------------------

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

            print(f"✅ Telegram message sent successfully to {chat_id}")

        except Exception as e:

            print(f"❌ Telegram error for {chat_id}: {e}")


# --------------------------------------------------
# CHECK PERU STATUS
# --------------------------------------------------

def get_peru_status():

    response = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(" ", strip=True)

    peru_position = text.lower().find("peru")

    if peru_position == -1:

        return "UNKNOWN"

    section = text[
        peru_position:
        peru_position + 150
    ].lower()

    if "paused" in section:

        return "PAUSED"

    if "open" in section:

        return "OPEN"

    if "closed" in section:

        return "CLOSED"

    return "UNKNOWN"


# --------------------------------------------------
# STATE
# --------------------------------------------------

def load_state():

    if os.path.exists(STATE_FILE):

        with open(STATE_FILE, "r") as file:

            return json.load(file)

    return {
        "previous_status": "UNKNOWN"
    }


def save_state(state):

    with open(STATE_FILE, "w") as file:

        json.dump(
            state,
            file,
            indent=2
        )


# --------------------------------------------------
# TEST MESSAGE
# --------------------------------------------------

def test_message():

    message = """🧪🇦🇺 AUSTRALIA 462 TEST MESSAGE

Your Peru visa checker is working.

This message was sent to ALL configured Telegram accounts.

The system is configured to:

🔎 Check Peru every 5 minutes
🚨 Alert immediately if Peru opens
⏰ Send an update every 30 minutes while OPEN
🌅 Send a morning status at 08:00 UK
🌙 Send a night status at 23:00 UK

Telegram test successful."""

    send_telegram(message)

    print("🧪 TEST MESSAGE COMPLETED")


# --------------------------------------------------
# NORMAL 5-MINUTE CHECK
# --------------------------------------------------

def check_status():

    now = datetime.now(UK_TZ)

    status = get_peru_status()

    state = load_state()

    previous_status = state.get(
        "previous_status",
        "UNKNOWN"
    )

    print(f"🇦🇺 Peru status: {status}")
    print(f"🇬🇧 UK time: {now}")
    print(f"Previous status: {previous_status}")


    # ----------------------------------------------
    # OPEN ALERT
    # ----------------------------------------------

    if status == "OPEN" and previous_status != "OPEN":

        message = """🚨🇦🇺 AUSTRALIA 462 VISA IS OPEN! 🇵🇪

Peru's Work and Holiday (subclass 462) cap is now OPEN.

APPLY NOW!

Official Home Affairs page:
https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"""

        send_telegram(message)

        print("🚨 OPEN ALERT SENT!")


    # ----------------------------------------------
    # SAVE CURRENT STATUS
    # ----------------------------------------------

    state["previous_status"] = status

    save_state(state)

    print("✅ Status check completed")


# --------------------------------------------------
# 30-MINUTE OPEN UPDATE
# --------------------------------------------------

def open_update():

    status = get_peru_status()

    now = datetime.now(UK_TZ)

    print(f"🇦🇺 Peru status: {status}")
    print(f"🇬🇧 UK time: {now}")

    if status == "OPEN":

        message = """🚨🇦🇺 AUSTRALIA 462 UPDATE

Peru's Work and Holiday (subclass 462) cap is STILL OPEN! 🇵🇪

If you are eligible, check the official Home Affairs website and apply as soon as possible.

Official page:
https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"""

        send_telegram(message)

        print("⏰ 30-MINUTE OPEN UPDATE SENT!")

    else:

        print("ℹ️ Peru is not OPEN — no 30-minute message sent")


# --------------------------------------------------
# MORNING MESSAGE
# --------------------------------------------------

def morning_update():

    status = get_peru_status()

    now = datetime.now(UK_TZ)

    if status == "OPEN":

        status_text = "🚨 OPEN — Peru's cap is currently OPEN!"

    elif status == "PAUSED":

        status_text = "⏸️ PAUSED — Peru's cap is currently PAUSED."

    elif status == "CLOSED":

        status_text = "🔴 CLOSED — Peru's cap is currently CLOSED."

    else:

        status_text = f"❓ Current status: {status}"


    message = f"""🌅🇦🇺 AUSTRALIA 462 MORNING UPDATE

Date: {now.strftime("%Y-%m-%d")}

🇵🇪 Peru status:

{status_text}

🔎 The checker is monitoring Peru every 5 minutes.

Official Home Affairs page:
https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"""

    send_telegram(message)

    print("🌅 MORNING MESSAGE SENT!")


# --------------------------------------------------
# NIGHT MESSAGE
# --------------------------------------------------

def night_update():

    status = get_peru_status()

    now = datetime.now(UK_TZ)

    if status == "OPEN":

        status_text = "🚨 OPEN — Peru's cap is currently OPEN!"

    elif status == "PAUSED":

        status_text = "⏸️ PAUSED — Peru's cap is currently PAUSED."

    elif status == "CLOSED":

        status_text = "🔴 CLOSED — Peru's cap is currently CLOSED."

    else:

        status_text = f"❓ Current status: {status}"


    message = f"""🌙🇦🇺 AUSTRALIA 462 NIGHT UPDATE

Date: {now.strftime("%Y-%m-%d")}

🇵🇪 Peru status:

{status_text}

🔎 The checker will continue monitoring Peru every 5 minutes overnight.

Official Home Affairs page:
https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"""

    send_telegram(message)

    print("🌙 NIGHT MESSAGE SENT!")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

mode = os.environ.get(
    "CHECK_MODE",
    "check"
)


print(f"Running mode: {mode}")


if mode == "test":

    test_message()

elif mode == "check":

    check_status()

elif mode == "open_update":

    open_update()

elif mode == "morning":

    morning_update()

elif mode == "night":

    night_update()

else:

    print(f"❌ Unknown CHECK_MODE: {mode}")
    exit(1)
