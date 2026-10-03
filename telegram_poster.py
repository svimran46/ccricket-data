import os
import re
import json
import requests

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@sportzfyplay")
HISTORY_FILE = "posted_matches.json"

ALLOWED_SPORTS = {"football", "cricket"}

SPORT_META = {
    "football": {
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

def send_telegram_request(endpoint, payload):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{endpoint}"
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

def post_match_to_telegram(match):
    sport = (match.get("sport") or "").lower().strip()
    meta = SPORT_META.get(sport, {"emoji": "🏆", "title": "Sports Live", "tags": "#Sports #SportzfyPlay"})
    
    event_name = match.get("eventName")
    home = match.get("homeTeam") or ""
    away = match.get("awayTeam") or ""
    if not event_name:
        event_name = f"{home} vs {away}".strip() if (home and away) else "Live Match"

    slug = match.get("slug") or match.get("id")
    match_url = f"https://sportzfyplay.com/matches/{slug}"
    
    start_time = match.get("startTime", "Soon")
    match_date = match.get("matchDate", "")
    
    caption = (
        f"{meta['emoji']} <b>{event_name}</b>\n\n"
        f"🏆 <b>Category:</b> {meta['title']}\n"
    )
    if match_date:
        caption += f"📅 <b>Date:</b> {match_date}\n"
    if start_time:
        caption += f"⏰ <b>Time:</b> {start_time} UTC\n"
        
    caption += (
        f"\n▶️ <b>Watch Free in HD:</b>\n"
        f"🔗 <a href=\"{match_url}\">Click Here to Stream Live</a>\n\n"
        f"{meta['tags']}"
    )

    poster = match.get("poster")
    if poster and str(poster).startswith("http"):
        # Try sending photo with caption
        print(f"Attempting sendPhoto for: {event_name}")
        success = send_telegram_request("sendPhoto", {
            "chat_id": CHANNEL_ID,
            "photo": poster,
            "caption": caption,
            "parse_mode": "HTML"
        })
        if success:
            return True
        print(f"Photo failed, falling back to sendMessage for: {event_name}")

    # Fallback to sendMessage (text only)
    return send_telegram_request("sendMessage", {
        "chat_id": CHANNEL_ID,
        "text": caption,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
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

    print(f"Channel target: {CHANNEL_ID}")
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
    for key, match in unique_matches.items():
        sport = (match.get("sport") or "").lower().strip()
        
        # Only Football and Cricket
        if sport not in ALLOWED_SPORTS:
            continue

        if key in posted:
            continue

        print(f"🚀 Posting {sport.upper()} match: {match.get('eventName')} ({key})")
        if post_match_to_telegram(match):
            posted.add(key)
            new_posts += 1
            print(f"✅ Successfully posted {key}")
        else:
            errors += 1
            print(f"❌ Failed to post {key}")

    print(f"Finished. Posted {new_posts} new matches. Errors: {errors}")
    save_posted(posted)

    if errors > 0 and new_posts == 0:
        raise RuntimeError(f"Failed to post {errors} matches to Telegram. Check the error logs above for details.")

if __name__ == "__main__":
    main()
