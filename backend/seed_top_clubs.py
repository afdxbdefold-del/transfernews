"""
Seed-Skript für bekannte Top-Vereine
Fügt Weltklasse-Vereine zur Datenbank hinzu, damit Trending-Links funktionieren
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Top-Vereine mit Details
TOP_CLUBS_DATA = [
    # England - Premier League
    {
        "name": "Manchester City",
        "slug": "manchester-city",
        "aliases": ["man city", "city", "manchester city"],
        "country": "England",
        "league": "Premier League",
        "founded": 1880
    },
    {
        "name": "Arsenal",
        "slug": "arsenal",
        "aliases": ["arsenal", "arsenal fc", "the gunners"],
        "country": "England",
        "league": "Premier League",
        "founded": 1886
    },
    {
        "name": "Liverpool",
        "slug": "liverpool",
        "aliases": ["liverpool", "liverpool fc", "the reds"],
        "country": "England",
        "league": "Premier League",
        "founded": 1892
    },
    {
        "name": "Manchester United",
        "slug": "manchester-united",
        "aliases": ["man united", "united", "manchester united", "man utd"],
        "country": "England",
        "league": "Premier League",
        "founded": 1878
    },
    {
        "name": "Chelsea",
        "slug": "chelsea",
        "aliases": ["chelsea", "chelsea fc", "the blues"],
        "country": "England",
        "league": "Premier League",
        "founded": 1905
    },
    {
        "name": "Tottenham Hotspur",
        "slug": "tottenham",
        "aliases": ["tottenham", "spurs", "tottenham hotspur"],
        "country": "England",
        "league": "Premier League",
        "founded": 1882
    },
    {
        "name": "Newcastle United",
        "slug": "newcastle",
        "aliases": ["newcastle", "newcastle united", "the magpies"],
        "country": "England",
        "league": "Premier League",
        "founded": 1892
    },
    {
        "name": "Aston Villa",
        "slug": "aston-villa",
        "aliases": ["aston villa", "villa"],
        "country": "England",
        "league": "Premier League",
        "founded": 1874
    },
    {
        "name": "West Ham United",
        "slug": "west-ham",
        "aliases": ["west ham", "west ham united", "the hammers"],
        "country": "England",
        "league": "Premier League",
        "founded": 1895
    },
    
    # Spain - La Liga
    {
        "name": "Real Madrid",
        "slug": "real-madrid",
        "aliases": ["real madrid", "real", "madrid", "los blancos"],
        "country": "Spain",
        "league": "La Liga",
        "founded": 1902
    },
    {
        "name": "FC Barcelona",
        "slug": "barcelona",
        "aliases": ["barcelona", "barca", "fc barcelona", "barça"],
        "country": "Spain",
        "league": "La Liga",
        "founded": 1899
    },
    {
        "name": "Atlético Madrid",
        "slug": "atletico-madrid",
        "aliases": ["atletico", "atletico madrid", "atlético madrid"],
        "country": "Spain",
        "league": "La Liga",
        "founded": 1903
    },
    
    # Germany - Bundesliga
    {
        "name": "Bayern München",
        "slug": "bayern-muenchen",
        "aliases": ["bayern", "bayern münchen", "bayern munich", "fc bayern"],
        "country": "Germany",
        "league": "Bundesliga",
        "founded": 1900
    },
    {
        "name": "Borussia Dortmund",
        "slug": "borussia-dortmund",
        "aliases": ["dortmund", "bvb", "borussia dortmund"],
        "country": "Germany",
        "league": "Bundesliga",
        "founded": 1909
    },
    {
        "name": "RB Leipzig",
        "slug": "rb-leipzig",
        "aliases": ["leipzig", "rb leipzig", "rasenballsport leipzig"],
        "country": "Germany",
        "league": "Bundesliga",
        "founded": 2009
    },
    {
        "name": "Bayer Leverkusen",
        "slug": "bayer-leverkusen",
        "aliases": ["leverkusen", "bayer leverkusen", "bayer 04"],
        "country": "Germany",
        "league": "Bundesliga",
        "founded": 1904
    },
    {
        "name": "Eintracht Frankfurt",
        "slug": "eintracht-frankfurt",
        "aliases": ["frankfurt", "eintracht", "eintracht frankfurt", "sge"],
        "country": "Germany",
        "league": "Bundesliga",
        "founded": 1899
    },
    {
        "name": "VfB Stuttgart",
        "slug": "vfb-stuttgart",
        "aliases": ["stuttgart", "vfb stuttgart", "vfb"],
        "country": "Germany",
        "league": "Bundesliga",
        "founded": 1893
    },
    {
        "name": "Borussia Mönchengladbach",
        "slug": "borussia-moenchengladbach",
        "aliases": ["gladbach", "mönchengladbach", "borussia mönchengladbach", "bmg"],
        "country": "Germany",
        "league": "Bundesliga",
        "founded": 1900
    },
    {
        "name": "VfL Wolfsburg",
        "slug": "vfl-wolfsburg",
        "aliases": ["wolfsburg", "vfl wolfsburg"],
        "country": "Germany",
        "league": "Bundesliga",
        "founded": 1945
    },
    
    # Italy - Serie A
    {
        "name": "Inter Mailand",
        "slug": "inter-mailand",
        "aliases": ["inter", "inter mailand", "inter milan", "internazionale"],
        "country": "Italy",
        "league": "Serie A",
        "founded": 1908
    },
    {
        "name": "AC Milan",
        "slug": "ac-milan",
        "aliases": ["milan", "ac milan", "ac mailand"],
        "country": "Italy",
        "league": "Serie A",
        "founded": 1899
    },
    {
        "name": "Juventus Turin",
        "slug": "juventus",
        "aliases": ["juventus", "juve", "juventus turin"],
        "country": "Italy",
        "league": "Serie A",
        "founded": 1897
    },
    {
        "name": "SSC Neapel",
        "slug": "neapel",
        "aliases": ["napoli", "neapel", "ssc napoli", "ssc neapel"],
        "country": "Italy",
        "league": "Serie A",
        "founded": 1926
    },
    {
        "name": "AS Rom",
        "slug": "as-rom",
        "aliases": ["roma", "rom", "as roma", "as rom"],
        "country": "Italy",
        "league": "Serie A",
        "founded": 1927
    },
    
    # France - Ligue 1
    {
        "name": "Paris Saint-Germain",
        "slug": "paris-saint-germain",
        "aliases": ["psg", "paris", "paris saint-germain"],
        "country": "France",
        "league": "Ligue 1",
        "founded": 1970
    },
    {
        "name": "Olympique Marseille",
        "slug": "olympique-marseille",
        "aliases": ["marseille", "om", "olympique marseille"],
        "country": "France",
        "league": "Ligue 1",
        "founded": 1899
    },
    {
        "name": "AS Monaco",
        "slug": "as-monaco",
        "aliases": ["monaco", "as monaco"],
        "country": "France",
        "league": "Ligue 1",
        "founded": 1924
    },
    
    # Other
    {
        "name": "Al-Nassr",
        "slug": "al-nassr",
        "aliases": ["al nassr", "al-nassr"],
        "country": "Saudi Arabia",
        "league": "Saudi Pro League",
        "founded": 1955
    },
    {
        "name": "Al-Hilal",
        "slug": "al-hilal",
        "aliases": ["al hilal", "al-hilal"],
        "country": "Saudi Arabia",
        "league": "Saudi Pro League",
        "founded": 1957
    },
    {
        "name": "Inter Miami",
        "slug": "inter-miami",
        "aliases": ["inter miami", "miami"],
        "country": "USA",
        "league": "MLS",
        "founded": 2018
    },
]


async def seed_top_clubs():
    """Seed top clubs to database"""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    now = datetime.now(timezone.utc).isoformat()
    added = 0
    updated = 0
    
    for club_data in TOP_CLUBS_DATA:
        # Check if club already exists
        existing = await db.clubs.find_one({"slug": club_data["slug"]})
        
        club_doc = {
            "name": club_data["name"],
            "slug": club_data["slug"],
            "aliases": club_data["aliases"],
            "country": club_data["country"],
            "league": club_data["league"],
            "founded": club_data["founded"],
            "logo": None,
            "meta_title": f"{club_data['name']} Transfer-News | transfernews.de",
            "meta_description": f"Aktuelle Transfer-Gerüchte und News zu {club_data['name']}.",
            "updated_at": now
        }
        
        if existing:
            # Update existing club
            await db.clubs.update_one(
                {"slug": club_data["slug"]},
                {"$set": club_doc}
            )
            updated += 1
            print(f"Updated: {club_data['name']}")
        else:
            # Create new club
            club_doc["id"] = str(uuid.uuid4())
            club_doc["created_at"] = now
            await db.clubs.insert_one(club_doc)
            added += 1
            print(f"Added: {club_data['name']}")
    
    print(f"\nDone! Added: {added}, Updated: {updated}")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_top_clubs())
