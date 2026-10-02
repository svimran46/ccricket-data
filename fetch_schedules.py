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

# Official tournament & host-board broadcaster mapping by territory
BROADCASTER_REGISTRY = [
    # ICC Tournaments & Qualifiers
    {
        "keywords": ["world cup", "champions trophy", "wtc", "world test championship", "qualifier", "league two"],
        "broadcasters": {
            "India / Subcontinent": "Star Sports Network, Disney+ Hotstar, FanCode (Qualifiers)",
            "UK": "Sky Sports Cricket",
            "USA / Canada": "Willow TV",
            "Australia": "Prime Video / Fox Cricket",
            "South Africa": "SuperSport",
            "Global / Digital": "ICC.tv"
        }
    },
    # Asian Games
    {
        "keywords": ["asian games"],
        "broadcasters": {
            "India / Subcontinent": "Sony Sports Network, Sony LIV",
            "Host / Asia": "Asian Games Broadcasting Network, TBS",
            "Global": "Olympic Channel / Official Regional Broadcasters"
        }
    },
    # Indian Premier League
    {
        "keywords": ["ipl", "indian premier league", "wpl", "women's premier league"],
        "broadcasters": {
            "India": "Star Sports (TV), JioCinema (Digital)",
            "UK": "Sky Sports Cricket",
            "USA / Canada": "Willow TV",
            "Australia": "Fox Cricket / Kayo",
            "South Africa": "SuperSport"
        }
    },
    # Big Bash League & Australian Domestic
    {
        "keywords": ["big bash", "bbl", "wbbl", "sheffield shield", "marsh cup"],
        "broadcasters": {
            "Australia": "Seven Network (TV), Fox Cricket, Kayo Sports, cricket.com.au",
            "India": "Star Sports / Disney+ Hotstar",
            "UK": "Sky Sports Cricket",
            "USA": "Willow TV"
        }
    },
    # Pakistan Super League
    {
        "keywords": ["psl", "pakistan super league"],
        "broadcasters": {
            "Pakistan": "A Sports, Ten Sports, Tamasha (Digital)",
            "India": "Sony Sports Network, Sony LIV",
            "UK": "Sky Sports Cricket",
            "USA": "Willow TV"
        }
    },
    # South African Cricket & SA20
    {
        "keywords": ["sa20", "csa t20", "csa", "south africa domestic"],
        "broadcasters": {
            "South Africa": "SuperSport",
            "India": "Sports18, JioCinema",
            "UK": "Sky Sports Cricket",
            "USA": "Willow TV"
        }
    },
    # Caribbean Premier League
    {
        "keywords": ["cpl", "caribbean premier league"],
        "broadcasters": {
            "Caribbean": "Flow Sports, SportsMax",
            "India": "Star Sports, FanCode",
            "UK": "TNT Sports",
            "USA": "Willow TV"
        }
    },
    # English Cricket & The Hundred
    {
        "keywords": ["the hundred", "vitality blast", "county championship"],
        "broadcasters": {
            "UK": "Sky Sports Cricket, BBC Sport",
            "India": "Sony Sports Network / FanCode",
            "USA": "Willow TV",
            "Australia": "Fox Cricket"
        }
    },
    # Legends Tournaments
    {
        "keywords": ["legends", "world championship of legends", "road safety"],
        "broadcasters": {
            "India": "Star Sports, FanCode",
            "UK": "TNT Sports",
            "USA": "Willow TV"
        }
    },
    # Bilateral Tours by Host Country
    {
        "keywords": ["tour of india", "irani cup", "ranji trophy", "deodhar trophy"],
        "broadcasters": {
            "India (Host)": "Sports18 (TV), JioCinema (Digital)",
            "UK": "TNT Sports / Sky Sports",
            "USA / Canada": "Willow TV",
            "Subcontinent": "Sports18 / Regional Feeds"
        }
    },
    {
        "keywords": ["tour of australia"],
        "broadcasters": {
            "Australia (Host)": "Seven Network (Free-to-Air), Fox Cricket, Kayo",
            "India": "Star Sports Network",
            "UK": "TNT Sports",
            "USA": "Willow TV"
        }
    },
    {
        "keywords": ["tour of england"],
        "broadcasters": {
            "UK (Host)": "Sky Sports Cricket, BBC",
            "India": "Sony Sports Network, Sony LIV",
            "USA": "Willow TV",
            "Australia": "Fox Cricket"
        }
    },
    {
        "keywords": ["tour of south korea", "korea"],
        "broadcasters": {
            "Korea / Regional": "Korea Cricket Association Channel / Local Sports",
            "Global / Subcontinent": "ICC.tv / FanCode"
        }
    },
    {
        "keywords": ["tour of south africa"],
        "broadcasters": {
            "South Africa (Host)": "SuperSport",
            "India": "Sports18 / Star Sports",
            "UK": "Sky Sports Cricket"
        }
    },
    {
        "keywords": ["tour of pakistan"],
        "broadcasters": {
            "Pakistan (Host)": "PTV Sports, A Sports, Ten Sports",
            "India": "Sony Sports Network",
            "UK": "Sky Sports Cricket"
        }
    },
    {
        "keywords": ["tour of west indies"],
        "broadcasters": {
            "Caribbean (Host)": "Flow Sports, Rush",
            "India": "FanCode",
            "USA": "Willow TV"
        }
    },
    {
        "keywords": ["tour of new zealand"],
        "broadcasters": {
            "New Zealand (Host)": "TVNZ, Spark Sport",
            "India": "Sony Sports Network / Prime Video",
            "UK": "TNT Sports"
        }
    }
]

def resolve_broadcasters(series_name, match_desc="", venue_info={}):
    """Determine official TV & digital broadcaster names based on series/tournament rights."""
    combined_text = f"{series_name} {match_desc} {venue_info.get('country', '')}".lower()
    
    for item in BROADCASTER_REGISTRY:
        if any(kw in combined_text for kw in item["keywords"]):
            return item["broadcasters"]

    # General default for international / associate cricket
    return {
        "Global / Digital": "ICC.tv / Official Board YouTube & OTT",
        "Subcontinent": "FanCode / Local Sports Network",
        "USA / International": "Willow TV / Local Sports Feeds"
    }

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
        f"CRICKET MATCH SCHEDULES & OFFICIAL BROADCASTERS",
        f"Generated: {now_utc}",
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

                    # Get official broadcasters
                    broadcasters = resolve_broadcasters(series_name, match_desc, m.get("venueInfo", {}))

                    lines.append(f"  • Series: {series_name}")
                    lines.append(f"    Match : {match_desc} - {team1} vs {team2}")
                    lines.append(f"    Time  : {time_str}")
                    lines.append(f"    Venue : {venue_display}")
                    lines.append(f"    Status: {status}")
                    lines.append(f"    Official Broadcasters:")
                    for region, channels in broadcasters.items():
                        lines.append(f"      - {region}: {channels}")
                    lines.append("")

                    cat_count += 1
                    total_matches += 1

        print(f"  Found {cat_count} matches for {cat_name}")

    with open("schedules.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nDone! Successfully written {total_matches} matches with broadcaster data to schedules.txt")

if __name__ == "__main__":
    main()
