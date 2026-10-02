import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

API_KEY = os.getenv("RAPIDAPI_KEY", "42ecd493efmshc020cf870aba741p15aafdjsndaea2b0e74a4")
API_HOST = "cricbuzz-cricket.p.rapidapi.com"

CATEGORIES = [
    ("INTERNATIONAL", "https://cricbuzz-cricket.p.rapidapi.com/schedule/v1/international"),
    ("T20 LEAGUES", "https://cricbuzz-cricket.p.rapidapi.com/schedule/v1/league"),
    ("DOMESTIC", "https://cricbuzz-cricket.p.rapidapi.com/schedule/v1/domestic")
]

def fetch_schedule(url):
    req = urllib.request.Request(
        url,
        headers={
            "X-RapidAPI-Host": API_HOST,
            "X-RapidAPI-Key": API_KEY
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code} for {url}: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    lines = [
        "============================================================",
        f"CRICKET MATCH SCHEDULES (Generated: {now_utc})",
        "============================================================",
        ""
    ]

    total_matches = 0

    for cat_name, cat_url in CATEGORIES:
        print(f"Fetching {cat_name} matches...")
        data = fetch_schedule(cat_url)
        if not data:
            continue

        schedule_blocks = data.get("matchScheduleMap", [])
        lines.append(f"############################################################")
        lines.append(f"  CATEGORY: {cat_name}")
        lines.append(f"############################################################\n")

        cat_count = 0
        for block in schedule_blocks:
            wrapper = block.get("scheduleAdWrapper")
            if not wrapper:
                continue

            date_str = wrapper.get("date")
            match_list = wrapper.get("matchScheduleList", [])

            if not match_list:
                continue

            lines.append(f"--- Date: {date_str or 'Upcoming'} ---")

            for item in match_list:
                series_name = item.get("seriesName", "Unknown Series")
                matches = item.get("matchInfo", [])

                for m in matches:
                    team1 = m.get("team1", {}).get("teamName", "TBA")
                    team2 = m.get("team2", {}).get("teamName", "TBA")
                    match_desc = m.get("matchDesc", "")
                    status = m.get("status", "Scheduled")
                    venue = m.get("venueInfo", {}).get("ground", "")
                    city = m.get("venueInfo", {}).get("city", "")
                    start_date = m.get("startDate", "")

                    venue_display = f"{venue}, {city}" if venue and city else (venue or city or "TBA")
                    
                    if start_date:
                        try:
                            dt = datetime.fromtimestamp(int(start_date) / 1000, tz=timezone.utc)
                            time_str = dt.strftime("%Y-%m-%d %H:%M UTC")
                        except Exception:
                            time_str = str(start_date)
                    else:
                        time_str = "TBA"

                    lines.append(f"  • Series: {series_name}")
                    lines.append(f"    Match : {match_desc} - {team1} vs {team2}")
                    lines.append(f"    Time  : {time_str}")
                    lines.append(f"    Venue : {venue_display}")
                    lines.append(f"    Status: {status}")
                    lines.append("")

                    cat_count += 1
                    total_matches += 1

        print(f"  Found {cat_count} matches for {cat_name}")

    with open("schedules.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nDone! Successfully written {total_matches} matches to schedules.txt")

if __name__ == "__main__":
    main()
