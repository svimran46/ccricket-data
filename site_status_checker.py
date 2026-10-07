import os
import urllib.request
import json
import time
from datetime import datetime, timezone

TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
STATUS_CHANNEL_ID = os.getenv("DISCORD_STATUS_CHANNEL_ID", "1557457412716363797").strip()
TARGET_URL = "https://sportzfyplay.com"

HEADERS = {
    'Authorization': f'Bot {TOKEN}',
    'Content-Type': 'application/json',
    'User-Agent': 'DiscordBot (https://github.com/svimran46/ccricket-data, 1.0.0)'
}

def check_site():
    start = time.time()
    try:
        req = urllib.request.Request(
            TARGET_URL,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            elapsed_ms = int((time.time() - start) * 1000)
            if resp.status == 200:
                return True, resp.status, elapsed_ms
            return False, resp.status, elapsed_ms
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return False, str(e), elapsed_ms

def update_status():
    if not TOKEN:
        print("Note: DISCORD_BOT_TOKEN not provided, skipping Discord site status update.")
        return
    is_up, status_code, latency = check_site()
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if is_up:
        embed = {
            "title": "🟢 All Systems Operational",
            "description": f"**[sportzfyplay.com]({TARGET_URL})** is fully **ONLINE** and operational.",
            "color": 0x1ED760,  # Green
            "fields": [
                {"name": "Website Status", "value": "🟢 Online (HTTP 200 OK)", "inline": True},
                {"name": "Response Time", "value": f"⚡ {latency} ms", "inline": True},
                {"name": "Stream Servers", "value": "🟢 Operational", "inline": True},
            ],
            "footer": {"text": f"Last Checked: {now_utc} • Auto-refreshing"}
        }
        channel_name = "🟢・site-status"
    else:
        embed = {
            "title": "🔴 Service Outage Detected",
            "description": f"**[sportzfyplay.com]({TARGET_URL})** appears to be **OFFLINE** or experiencing high latency.",
            "color": 0xEF4444,  # Red
            "fields": [
                {"name": "Website Status", "value": f"🔴 Offline ({status_code})", "inline": True},
                {"name": "Response Time", "value": f"⚠️ {latency} ms", "inline": True},
                {"name": "Incident Details", "value": "Engineers are looking into it. Stay tuned for updates.", "inline": False},
            ],
            "footer": {"text": f"Incident Reported: {now_utc}"}
        }
        channel_name = "🔴・site-offline"

    # Update channel name dynamically to reflect live status
    try:
        patch_req = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{STATUS_CHANNEL_ID}",
            data=json.dumps({"name": channel_name}).encode('utf-8'),
            headers=HEADERS,
            method='PATCH'
        )
        urllib.request.urlopen(patch_req)
    except Exception as e:
        print("Note on channel rename:", e)

    # Check for existing bot message in the channel to edit instead of spamming new messages
    list_req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{STATUS_CHANNEL_ID}/messages?limit=5",
        headers=HEADERS
    )
    existing_msg_id = None
    try:
        with urllib.request.urlopen(list_req) as resp:
            msgs = json.loads(resp.read().decode('utf-8'))
            if msgs:
                existing_msg_id = msgs[0]['id']
    except Exception as e:
        print("Note on fetch msg:", e)

    payload = {"embeds": [embed]}

    if existing_msg_id:
        url = f"https://discord.com/api/v10/channels/{STATUS_CHANNEL_ID}/messages/{existing_msg_id}"
        method = 'PATCH'
    else:
        url = f"https://discord.com/api/v10/channels/{STATUS_CHANNEL_ID}/messages"
        method = 'POST'

    msg_req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=HEADERS,
        method=method
    )
    with urllib.request.urlopen(msg_req) as resp:
        print(f"Status card updated! (HTTP {resp.status}) - is_up={is_up}")

if __name__ == '__main__':
    update_status()
