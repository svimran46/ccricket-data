import os
import re
import json
import time
import html
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@sportzfyplay")
HISTORY_FILE = "posted_matches.json"

# Timezone that sportzfyplay.com uses for matchDate/startTime.
# Verified: UEFA qualifiers (20:45 CEST kick-off) are listed as 19:45 -> UK time.
# Europe/London handles GMT/BST daylight saving automatically.
SOURCE_TZ = ZoneInfo(os.getenv("SOURCE_TIMEZONE", "Europe/London"))

# Capital-city timezones shown in each post (flag, label, IANA zone)
DISPLAY_TIMEZONES = [
    ("🇧🇩", "Bangladesh (Dhaka)", "Asia/Dhaka"),
    ("🇮🇳", "India (New Delhi)", "Asia/Kolkata"),
    ("🇺🇸", "USA (Washington DC)", "America/New_York"),
    ("🇮🇩", "Indonesia (Jakarta)", "Asia/Jakarta"),
    ("🇳🇬", "Nigeria (Abuja)", "Africa/Lagos"),
    ("🇸🇬", "Singapore", "Asia/Singapore"),
]

ALLOWED_SPORTS = {"football", "soccer", "cricket"}

SPORT_META = {
    "football": {
        "emoji": "⚽",
        "title": "Football Live",
        "tags": "#Football #LiveStream #SportzfyPlay"
    },
    "soccer": {
        "emoji": "⚽",
        "title": "Football Live",
        "tags": "#Football #LiveStream #SportzfyPlay"
    },
    "cricket": {
        "emoji": "🏏",
        "title": "Cricket Live",
        "tags": "#Cricket #LiveStream #SportzfyPlay"
    }
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def load_posted():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data)
        except Exception as e:
            print(f"Warning: Could not read history file: {e}")
            return set()
    return set()

def save_posted(posted_set):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(posted_set)), f, indent=2)

def get_clean_token():
    token = (BOT_TOKEN or "").strip().strip('"').strip("'")
    if token.lower().startswith("bot"):
        token = token[3:].strip()
    return token

def get_clean_channel():
    channel = (CHANNEL_ID or "").strip().strip('"').strip("'")
    if "t.me/" in channel:
        channel = "@" + channel.split("t.me/")[-1].strip("/")
    # Auto-add '@' if user omitted it on public username (not numeric ID)
    if channel and not channel.startswith("@") and not channel.startswith("-") and not channel.replace("-", "").isdigit():
        channel = "@" + channel
    return channel

def verify_bot():
    token = get_clean_token()
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN is empty!")
        return False
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        r = requests.get(url, timeout=15)
        res = r.json()
        if res.get("ok"):
            bot_info = res["result"]
            print(f"🤖 Connected successfully as Bot: @{bot_info.get('username')} ({bot_info.get('first_name')})")
            return True
        else:
            print(f"❌ Telegram Bot Token Invalid! Response: {res}")
            return False
    except Exception as e:
        print(f"❌ Failed to reach Telegram API: {e}")
        return False

def send_telegram_request(endpoint, payload):
    token = get_clean_token()
    url = f"https://api.telegram.org/bot{token}/{endpoint}"
    payload["chat_id"] = get_clean_channel()
    try:
        resp = requests.post(url, json=payload, timeout=25)
        res_json = resp.json()
        if not resp.ok or not res_json.get("ok"):
            print(f"❌ Telegram API Error on {endpoint}: {resp.status_code} - {resp.text}")
            return False
        return True
    except Exception as e:
        print(f"❌ Request Exception on {endpoint}: {e}")
        return False

def build_time_block(match_date, start_time):
    """Return HTML lines with kick-off time in each capital. Falls back to raw text if parsing fails."""
    try:
        kickoff = datetime.strptime(f"{match_date} {start_time}", "%Y-%m-%d %H:%M").replace(tzinfo=SOURCE_TZ)
    except (ValueError, TypeError):
        if start_time:
            return f"⏰ <b>Time:</b> {html.escape(f'{match_date} {start_time}'.strip())}\n"
        return ""

    lines = ["\n🕒 <b>Kick-off Time:</b>"]
    for flag, label, tz in DISPLAY_TIMEZONES:
        local = kickoff.astimezone(ZoneInfo(tz))
        # e.g. "00:45 · Sun 04 Oct" (date shown so day changes are clear)
        lines.append(f"{flag} {label}: <b>{local.strftime('%H:%M')}</b> · {local.strftime('%a %d %b')}")
    return "\n".join(lines) + "\n"

def post_match_to_telegram(match):
    sport = (match.get("sport") or "").lower().strip()
    meta = SPORT_META.get(sport, {"emoji": "🏆", "title": "Sports Live", "tags": "#Sports #SportzfyPlay"})
    
    event_name = match.get("eventName")
    home = match.get("homeTeam") or ""
    away = match.get("awayTeam") or ""
    if not event_name:
        event_name = f"{home} vs {away}".strip() if (home and away) else "Live Match"

    slug = str(match.get("slug") or match.get("id") or "").strip()
    if slug.startswith("/matches/"):
        slug = slug[9:]
    elif slug.startswith("matches/"):
        slug = slug[8:]
    slug = slug.strip("/")
    match_url = f"https://sportzfyplay.com/matches/{slug}"
    
    start_time = match.get("startTime") or ""
    match_date = match.get("matchDate") or ""

    # HTML-escape dynamic strings to prevent HTML parse crashes in Telegram
    safe_name = html.escape(str(event_name))
    safe_title = html.escape(str(meta['title']))

    caption = (
        f"{meta['emoji']} <b>{safe_name}</b>\n\n"
        f"🏆 <b>Category:</b> {safe_title}\n"
    )
    caption += build_time_block(match_date, start_time)
        
    caption += (
        f"\n▶️ <b>Watch Free in HD:</b>\n"
        f"🔗 <a href=\"{match_url}\">Click Here to Stream Live</a>\n\n"
        f"{meta['tags']}"
    )

    poster = match.get("poster")
    if poster and str(poster).startswith("http"):
        print(f"Attempting sendPhoto for: {event_name}")
        success = send_telegram_request("sendPhoto", {
            "chat_id": get_clean_channel(),
            "photo": poster,
            "caption": caption,
            "parse_mode": "HTML"
        })
        if success:
            return True
        print(f"Photo failed, falling back to sendMessage for: {event_name}")

    # Fallback to sendMessage (text only)
    return send_telegram_request("sendMessage", {
        "chat_id": get_clean_channel(),
        "text": caption,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    })

# ---------------------------------------------------------------- DISCORD ---

DISCORD_WEBHOOK_URL = (os.getenv("DISCORD_WEBHOOK_URL") or "").strip().strip('"').strip("'")
DISCORD_COLORS = {"football": 0x1ED760, "soccer": 0x1ED760, "cricket": 0x3B82F6}

def send_discord_webhook(payload, retries=3):
    """POST to the Discord webhook, honouring Discord's 429 rate-limit retry_after."""
    for attempt in range(retries):
        try:
            resp = requests.post(f"{DISCORD_WEBHOOK_URL}?wait=true", json=payload, timeout=25)
        except Exception as e:
            print(f"❌ Discord request exception: {e}")
            return False
        if resp.status_code == 429:
            try:
                wait = float(resp.json().get("retry_after", 2))
            except Exception:
                wait = 2.0
            print(f"⏳ Discord rate limited, retrying in {wait:.1f}s")
            time.sleep(wait + 0.5)
            continue
        if resp.ok:
            return True
        print(f"❌ Discord API Error: {resp.status_code} - {resp.text}")
        return False
    return False

def post_match_to_discord(match):
    sport = (match.get("sport") or "").lower().strip()
    meta = SPORT_META.get(sport, {"emoji": "🏆", "title": "Sports Live", "tags": ""})

    event_name = match.get("eventName")
    home = match.get("homeTeam") or ""
    away = match.get("awayTeam") or ""
    if not event_name:
        event_name = f"{home} vs {away}".strip() if (home and away) else "Live Match"

    slug = str(match.get("slug") or match.get("id") or "").strip()
    for prefix in ("/matches/", "matches/"):
        if slug.startswith(prefix):
            slug = slug[len(prefix):]
    slug = slug.strip("/")
    match_url = f"https://sportzfyplay.com/matches/{slug}"

    match_date = match.get("matchDate") or ""
    start_time = match.get("startTime") or ""

    description = f"🏆 **Category:** {meta['title']}\n"
    fields = []
    try:
        kickoff = datetime.strptime(f"{match_date} {start_time}", "%Y-%m-%d %H:%M").replace(tzinfo=SOURCE_TZ)
        unix = int(kickoff.timestamp())
        # Discord renders <t:...> in every viewer's OWN local time automatically
        description += f"🕒 **Your local time:** <t:{unix}:F> (<t:{unix}:R>)\n"
        for flag, label, tz in DISPLAY_TIMEZONES:
            local = kickoff.astimezone(ZoneInfo(tz))
            fields.append({
                "name": f"{flag} {label}",
                "value": f"**{local.strftime('%H:%M')}** · {local.strftime('%a %d %b')}",
                "inline": True,
            })
    except (ValueError, TypeError):
        if start_time:
            description += f"⏰ **Time:** {f'{match_date} {start_time}'.strip()}\n"

    description += f"\n▶️ **[Click Here to Stream Live in HD]({match_url})**"

    embed = {
        "title": f"{meta['emoji']} {event_name}"[:256],
        "url": match_url,
        "description": description[:4096],
        "color": DISCORD_COLORS.get(sport, 0xFACC15),
        "fields": fields,
        "footer": {"text": "SportzfyPlay • Free Live Sports"},
    }
    poster = match.get("poster")
    if poster and str(poster).startswith("http"):
        embed["image"] = {"url": poster}

    return send_discord_webhook({
        "username": "SportzfyPlay",
        "embeds": [embed],
        "allowed_mentions": {"parse": []},  # never ping @everyone/@here by accident
    })

def fetch_page_matches(url):
    matches = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        print(f"GET {url} -> Status {resp.status_code}")
        if not resp.ok:
            return matches

        matches_raw = re.findall(r'&quot;match&quot;:\[0,(\{.*?\})\]', resp.text)
        print(f"Found {len(matches_raw)} raw matches in {url}")
        for raw in matches_raw:
            clean = raw.replace('&quot;', '"')
            try:
                data = json.loads(clean)
                m = {k: v[1] if isinstance(v, list) and len(v) > 1 else v for k, v in data.items()}
                matches.append(m)
            except Exception:
                continue
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return matches

def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ ERROR: TELEGRAM_BOT_TOKEN secret is not set in GitHub repository secrets!")
    if not CHANNEL_ID:
        raise SystemExit("❌ ERROR: TELEGRAM_CHANNEL_ID secret is not set in GitHub repository secrets!")

    if not verify_bot():
        raise SystemExit("❌ ERROR: Could not connect to Telegram bot! Check your TELEGRAM_BOT_TOKEN in GitHub secrets.")

    print(f"🎯 Target channel: {get_clean_channel()}")
    posted = load_posted()
    print(f"Currently remembered matches: {len(posted)}")

    all_found = []
    all_found.extend(fetch_page_matches("https://sportzfyplay.com/"))
    all_found.extend(fetch_page_matches("https://sportzfyplay.com/schedule"))

    # De-duplicate matches
    unique_matches = {}
    for m in all_found:
        key = m.get("slug") or m.get("id")
        if key and key not in unique_matches:
            unique_matches[key] = m

    print(f"Total unique matches scraped: {len(unique_matches)}")

    new_posts = 0
    errors = 0
    discord_enabled = DISCORD_WEBHOOK_URL.startswith("https://")
    print(f"💬 Discord posting: {'ENABLED' if discord_enabled else 'disabled (DISCORD_WEBHOOK_URL not set)'}")

    for key, match in unique_matches.items():
        sport = (match.get("sport") or "").lower().strip()

        # Only Football and Cricket
        if sport not in ALLOWED_SPORTS:
            continue

        # History keys: plain slug = Telegram (kept for backward compatibility), "discord:<slug>" = Discord
        if key not in posted:
            print(f"🚀 [Telegram] Posting {sport.upper()} match: {match.get('eventName')} ({key})")
            if post_match_to_telegram(match):
                posted.add(key)
                new_posts += 1
                print(f"✅ [Telegram] Posted {key}")
                time.sleep(2)  # anti-flood
            else:
                errors += 1
                print(f"❌ [Telegram] Failed {key}")

        discord_key = f"discord:{key}"
        if discord_enabled and discord_key not in posted:
            print(f"🚀 [Discord] Posting {sport.upper()} match: {match.get('eventName')} ({key})")
            if post_match_to_discord(match):
                posted.add(discord_key)
                new_posts += 1
                print(f"✅ [Discord] Posted {key}")
                time.sleep(1)
            else:
                errors += 1
                print(f"❌ [Discord] Failed {key}")

    print(f"Finished. Posted {new_posts} new messages. Errors: {errors}")
    save_posted(posted)

    if errors > 0 and new_posts == 0:
        raise RuntimeError(f"Failed to post {errors} messages. Check the error logs above for details.")

if __name__ == "__main__":
    main()
