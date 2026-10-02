import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

API_KEY = os.getenv("RAPIDAPI_KEY", "42ecd493efmshc020cf870aba741p15aafdjsndaea2b0e74a4")
API_HOST = "cricbuzz-cricket.p.rapidapi.com"
GITHUB_USER = "svimran46"
GITHUB_REPO = "ccricket-data"
REPO_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/assets/logos"

CATEGORIES = [
    ("International", "https://cricbuzz-cricket.p.rapidapi.com/schedule/v1/international"),
    ("T20 Leagues", "https://cricbuzz-cricket.p.rapidapi.com/schedule/v1/league"),
    ("Domestic", "https://cricbuzz-cricket.p.rapidapi.com/schedule/v1/domestic")
]

# Map channel names to clean repository vector logo URLs
LOGO_MAP = {
    "Star Sports": f"{REPO_RAW_URL}/star_sports.svg",
    "Disney+ Hotstar": f"{REPO_RAW_URL}/hotstar.svg",
    "Sony Sports Network": f"{REPO_RAW_URL}/sony_sports.svg",
    "Sony LIV": f"{REPO_RAW_URL}/sony_liv.svg",
    "Sports18": f"{REPO_RAW_URL}/sports18.svg",
    "JioCinema": f"{REPO_RAW_URL}/jiocinema.svg",
    "Sky Sports Cricket": f"{REPO_RAW_URL}/sky_sports.svg",
    "Willow TV": f"{REPO_RAW_URL}/willow_tv.svg",
    "SuperSport": f"{REPO_RAW_URL}/supersport.svg",
    "Fox Cricket": f"{REPO_RAW_URL}/fox_cricket.svg",
    "Seven Network": f"{REPO_RAW_URL}/channel7.svg",
    "TNT Sports": f"{REPO_RAW_URL}/tnt_sports.svg",
    "FanCode": f"{REPO_RAW_URL}/fancode.svg",
    "PTV Sports": f"{REPO_RAW_URL}/ptv_sports.svg",
    "ICC.tv": f"{REPO_RAW_URL}/icc_tv.svg",
}

BROADCASTER_REGISTRY = [
    {
        "keywords": ["world cup", "champions trophy", "wtc", "world test championship", "qualifier", "league two"],
        "broadcasters": [
            {"channel": "Star Sports", "region": "India / Subcontinent", "type": "TV", "logo": LOGO_MAP["Star Sports"]},
            {"channel": "Disney+ Hotstar", "region": "India / Subcontinent", "type": "Digital", "logo": LOGO_MAP["Disney+ Hotstar"]},
            {"channel": "Sky Sports Cricket", "region": "United Kingdom", "type": "TV & Digital", "logo": LOGO_MAP["Sky Sports Cricket"]},
            {"channel": "Willow TV", "region": "USA & Canada", "type": "TV & Digital", "logo": LOGO_MAP["Willow TV"]},
            {"channel": "Fox Cricket", "region": "Australia", "type": "TV & Digital", "logo": LOGO_MAP["Fox Cricket"]},
            {"channel": "SuperSport", "region": "South Africa", "type": "TV & Digital", "logo": LOGO_MAP["SuperSport"]},
            {"channel": "ICC.tv", "region": "Global", "type": "Digital", "logo": LOGO_MAP["ICC.tv"]}
        ]
    },
    {
        "keywords": ["asian games"],
        "broadcasters": [
            {"channel": "Sony Sports Network", "region": "India / Subcontinent", "type": "TV", "logo": LOGO_MAP["Sony Sports Network"]},
            {"channel": "Sony LIV", "region": "India / Subcontinent", "type": "Digital", "logo": LOGO_MAP["Sony LIV"]},
            {"channel": "Asian Games Network", "region": "Asia / Host", "type": "TV", "logo": None}
        ]
    },
    {
        "keywords": ["ipl", "indian premier league", "wpl"],
        "broadcasters": [
            {"channel": "Star Sports", "region": "India", "type": "TV", "logo": LOGO_MAP["Star Sports"]},
            {"channel": "JioCinema", "region": "India", "type": "Digital", "logo": LOGO_MAP["JioCinema"]},
            {"channel": "Sky Sports Cricket", "region": "United Kingdom", "type": "TV", "logo": LOGO_MAP["Sky Sports Cricket"]},
            {"channel": "Willow TV", "region": "USA & Canada", "type": "TV", "logo": LOGO_MAP["Willow TV"]},
            {"channel": "Fox Cricket", "region": "Australia", "type": "TV", "logo": LOGO_MAP["Fox Cricket"]}
        ]
    },
    {
        "keywords": ["big bash", "bbl", "wbbl", "sheffield shield", "marsh cup"],
        "broadcasters": [
            {"channel": "Seven Network", "region": "Australia", "type": "Free-to-Air TV", "logo": LOGO_MAP["Seven Network"]},
            {"channel": "Fox Cricket", "region": "Australia", "type": "Subscription TV", "logo": LOGO_MAP["Fox Cricket"]},
            {"channel": "Star Sports", "region": "India", "type": "TV", "logo": LOGO_MAP["Star Sports"]},
            {"channel": "Sky Sports Cricket", "region": "United Kingdom", "type": "TV", "logo": LOGO_MAP["Sky Sports Cricket"]},
            {"channel": "Willow TV", "region": "USA", "type": "TV", "logo": LOGO_MAP["Willow TV"]}
        ]
    },
    {
        "keywords": ["psl", "pakistan super league"],
        "broadcasters": [
            {"channel": "PTV Sports", "region": "Pakistan", "type": "TV", "logo": LOGO_MAP["PTV Sports"]},
            {"channel": "Sony Sports Network", "region": "India", "type": "TV", "logo": LOGO_MAP["Sony Sports Network"]},
            {"channel": "Sky Sports Cricket", "region": "United Kingdom", "type": "TV", "logo": LOGO_MAP["Sky Sports Cricket"]},
            {"channel": "Willow TV", "region": "USA", "type": "TV", "logo": LOGO_MAP["Willow TV"]}
        ]
    },
    {
        "keywords": ["sa20", "csa t20", "csa"],
        "broadcasters": [
            {"channel": "SuperSport", "region": "South Africa", "type": "TV", "logo": LOGO_MAP["SuperSport"]},
            {"channel": "Sports18", "region": "India", "type": "TV", "logo": LOGO_MAP["Sports18"]},
            {"channel": "JioCinema", "region": "India", "type": "Digital", "logo": LOGO_MAP["JioCinema"]},
            {"channel": "Sky Sports Cricket", "region": "United Kingdom", "type": "TV", "logo": LOGO_MAP["Sky Sports Cricket"]},
            {"channel": "Willow TV", "region": "USA", "type": "TV", "logo": LOGO_MAP["Willow TV"]}
        ]
    },
    {
        "keywords": ["tour of india", "irani cup", "ranji trophy"],
        "broadcasters": [
            {"channel": "Sports18", "region": "India (Host)", "type": "TV", "logo": LOGO_MAP["Sports18"]},
            {"channel": "JioCinema", "region": "India (Host)", "type": "Digital", "logo": LOGO_MAP["JioCinema"]},
            {"channel": "TNT Sports", "region": "United Kingdom", "type": "TV", "logo": LOGO_MAP["TNT Sports"]},
            {"channel": "Willow TV", "region": "USA & Canada", "type": "TV", "logo": LOGO_MAP["Willow TV"]}
        ]
    },
    {
        "keywords": ["tour of australia"],
        "broadcasters": [
            {"channel": "Seven Network", "region": "Australia (Host)", "type": "Free-to-Air", "logo": LOGO_MAP["Seven Network"]},
            {"channel": "Fox Cricket", "region": "Australia (Host)", "type": "TV & Digital", "logo": LOGO_MAP["Fox Cricket"]},
            {"channel": "Star Sports", "region": "India", "type": "TV", "logo": LOGO_MAP["Star Sports"]},
            {"channel": "TNT Sports", "region": "United Kingdom", "type": "TV", "logo": LOGO_MAP["TNT Sports"]},
            {"channel": "Willow TV", "region": "USA", "type": "TV", "logo": LOGO_MAP["Willow TV"]}
        ]
    },
    {
        "keywords": ["tour of england", "the hundred", "vitality blast"],
        "broadcasters": [
            {"channel": "Sky Sports Cricket", "region": "United Kingdom (Host)", "type": "TV", "logo": LOGO_MAP["Sky Sports Cricket"]},
            {"channel": "Sony Sports Network", "region": "India", "type": "TV", "logo": LOGO_MAP["Sony Sports Network"]},
            {"channel": "FanCode", "region": "India", "type": "Digital", "logo": LOGO_MAP["FanCode"]},
            {"channel": "Willow TV", "region": "USA", "type": "TV", "logo": LOGO_MAP["Willow TV"]}
        ]
    },
    {
        "keywords": ["legends", "world championship of legends"],
        "broadcasters": [
            {"channel": "Star Sports", "region": "India", "type": "TV", "logo": LOGO_MAP["Star Sports"]},
            {"channel": "FanCode", "region": "India", "type": "Digital", "logo": LOGO_MAP["FanCode"]},
            {"channel": "TNT Sports", "region": "United Kingdom", "type": "TV", "logo": LOGO_MAP["TNT Sports"]},
            {"channel": "Willow TV", "region": "USA", "type": "TV", "logo": LOGO_MAP["Willow TV"]}
        ]
    },
    {
        "keywords": ["korea", "indonesia"],
        "broadcasters": [
            {"channel": "ICC.tv", "region": "Global", "type": "Digital", "logo": LOGO_MAP["ICC.tv"]},
            {"channel": "FanCode", "region": "Subcontinent", "type": "Digital", "logo": LOGO_MAP["FanCode"]}
        ]
    }
]

def resolve_broadcasters(series_name, match_desc="", venue_info={}):
    combined = f"{series_name} {match_desc} {venue_info.get('country', '')}".lower()
    for entry in BROADCASTER_REGISTRY:
        if any(kw in combined for kw in entry["keywords"]):
            return entry["broadcasters"]

    return [
        {"channel": "ICC.tv", "region": "Global", "type": "Digital", "logo": LOGO_MAP["ICC.tv"]},
        {"channel": "FanCode", "region": "Subcontinent", "type": "Digital", "logo": LOGO_MAP["FanCode"]},
        {"channel": "Willow TV", "region": "USA & North America", "type": "Digital", "logo": LOGO_MAP["Willow TV"]}
    ]

def fetch_category_data(url):
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
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    now_utc = datetime.now(timezone.utc).isoformat()
    all_matches = []

    for cat_name, cat_url in CATEGORIES:
        print(f"Fetching {cat_name} matches...")
        data = fetch_category_data(cat_url)
        if not data:
            continue

        schedule_blocks = data.get("matchScheduleMap", [])
        for block in schedule_blocks:
            wrapper = block.get("scheduleAdWrapper")
            if not wrapper:
                continue

            date_str = wrapper.get("date")
            match_list = wrapper.get("matchScheduleList", [])

            for item in match_list:
                series_name = item.get("seriesName", "Unknown Series")
                matches = item.get("matchInfo", [])

                for m in matches:
                    team1_info = m.get("team1", {})
                    team2_info = m.get("team2", {})
                    venue_info = m.get("venueInfo", {})
                    start_date = m.get("startDate")

                    # Convert start timestamp to human-readable UTC
                    time_utc_str = None
                    epoch_millis = None
                    if start_date:
                        try:
                            epoch_millis = int(start_date)
                            dt = datetime.fromtimestamp(epoch_millis / 1000, tz=timezone.utc)
                            time_utc_str = dt.strftime("%Y-%m-%d %H:%M UTC")
                        except Exception:
                            time_utc_str = str(start_date)

                    broadcasters = resolve_broadcasters(series_name, m.get("matchDesc", ""), venue_info)

                    match_obj = {
                        "match_id": m.get("matchId"),
                        "category": cat_name,
                        "series": series_name,
                        "match_desc": m.get("matchDesc", ""),
                        "match_format": m.get("matchFormat", ""),
                        "status": m.get("status", "Scheduled"),
                        "schedule": {
                            "date": date_str,
                            "time_utc": time_utc_str,
                            "timestamp_millis": epoch_millis
                        },
                        "teams": {
                            "team1": {
                                "id": team1_info.get("teamId"),
                                "name": team1_info.get("teamName", "TBA"),
                                "short_name": team1_info.get("teamSName", "")
                            },
                            "team2": {
                                "id": team2_info.get("teamId"),
                                "name": team2_info.get("teamName", "TBA"),
                                "short_name": team2_info.get("teamSName", "")
                            }
                        },
                        "venue": {
                            "ground": venue_info.get("ground", ""),
                            "city": venue_info.get("city", ""),
                            "country": venue_info.get("country", "")
                        },
                        "broadcasters": broadcasters
                    }
                    all_matches.append(match_obj)

    # Master output structure
    output_data = {
        "metadata": {
            "title": "Cricket Match Schedules & Broadcasters",
            "last_updated_utc": now_utc,
            "total_matches": len(all_matches),
            "categories": [c[0] for c in CATEGORIES]
        },
        "matches": all_matches
    }

    # Write unified schedules.json
    json_path = "schedules.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nSUCCESS: Unified all {len(all_matches)} matches into {json_path}!")

if __name__ == "__main__":
    main()
