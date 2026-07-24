"""
Seed-Skript für bekannte Top-Spieler
Fügt Weltklasse-Spieler zur Datenbank hinzu, damit Trending-Links funktionieren
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

# Top-Spieler mit Details
TOP_PLAYERS_DATA = [
    # Tier 1 - Weltklasse
    {
        "name": "Kylian Mbappé",
        "slug": "mbappe",
        "aliases": ["mbappe", "kylian mbappe"],
        "country": "France",
        "birthdate": "1998-12-20",
        "position": "Forward",
        "current_club": "Real Madrid"
    },
    {
        "name": "Erling Haaland",
        "slug": "haaland",
        "aliases": ["haaland", "erling haaland"],
        "country": "Norway",
        "birthdate": "2000-07-21",
        "position": "Forward",
        "current_club": "Manchester City"
    },
    {
        "name": "Jude Bellingham",
        "slug": "bellingham",
        "aliases": ["bellingham", "jude bellingham"],
        "country": "England",
        "birthdate": "2003-06-29",
        "position": "Midfielder",
        "current_club": "Real Madrid"
    },
    {
        "name": "Vinícius Júnior",
        "slug": "vinicius",
        "aliases": ["vinicius", "vinicius junior", "vini jr"],
        "country": "Brazil",
        "birthdate": "2000-07-12",
        "position": "Forward",
        "current_club": "Real Madrid"
    },
    {
        "name": "Lionel Messi",
        "slug": "messi",
        "aliases": ["messi", "lionel messi", "leo messi"],
        "country": "Argentina",
        "birthdate": "1987-06-24",
        "position": "Forward",
        "current_club": "Inter Miami"
    },
    {
        "name": "Cristiano Ronaldo",
        "slug": "ronaldo",
        "aliases": ["ronaldo", "cristiano ronaldo", "cr7"],
        "country": "Portugal",
        "birthdate": "1985-02-05",
        "position": "Forward",
        "current_club": "Al-Nassr"
    },
    
    # Tier 2 - Top Stars
    {
        "name": "Mohamed Salah",
        "slug": "salah",
        "aliases": ["salah", "mohamed salah", "mo salah"],
        "country": "Egypt",
        "birthdate": "1992-06-15",
        "position": "Forward",
        "current_club": "Liverpool"
    },
    {
        "name": "Harry Kane",
        "slug": "kane",
        "aliases": ["kane", "harry kane"],
        "country": "England",
        "birthdate": "1993-07-28",
        "position": "Forward",
        "current_club": "Bayern München"
    },
    {
        "name": "Jamal Musiala",
        "slug": "musiala",
        "aliases": ["musiala", "jamal musiala"],
        "country": "Germany",
        "birthdate": "2003-02-26",
        "position": "Midfielder",
        "current_club": "Bayern München"
    },
    {
        "name": "Florian Wirtz",
        "slug": "wirtz",
        "aliases": ["wirtz", "florian wirtz"],
        "country": "Germany",
        "birthdate": "2003-05-03",
        "position": "Midfielder",
        "current_club": "Bayer Leverkusen"
    },
    {
        "name": "Bukayo Saka",
        "slug": "saka",
        "aliases": ["saka", "bukayo saka"],
        "country": "England",
        "birthdate": "2001-09-05",
        "position": "Forward",
        "current_club": "Arsenal"
    },
    {
        "name": "Cole Palmer",
        "slug": "palmer",
        "aliases": ["palmer", "cole palmer"],
        "country": "England",
        "birthdate": "2002-05-06",
        "position": "Midfielder",
        "current_club": "Chelsea"
    },
    {
        "name": "Kevin De Bruyne",
        "slug": "de-bruyne",
        "aliases": ["de bruyne", "kevin de bruyne", "kdb"],
        "country": "Belgium",
        "birthdate": "1991-06-28",
        "position": "Midfielder",
        "current_club": "Manchester City"
    },
    {
        "name": "Phil Foden",
        "slug": "foden",
        "aliases": ["foden", "phil foden"],
        "country": "England",
        "birthdate": "2000-05-28",
        "position": "Midfielder",
        "current_club": "Manchester City"
    },
    {
        "name": "Pedri",
        "slug": "pedri",
        "aliases": ["pedri", "pedri gonzalez"],
        "country": "Spain",
        "birthdate": "2002-11-25",
        "position": "Midfielder",
        "current_club": "Barcelona"
    },
    
    # Tier 3 - Bekannte Spieler
    {
        "name": "Neymar Jr",
        "slug": "neymar",
        "aliases": ["neymar", "neymar jr", "neymar junior"],
        "country": "Brazil",
        "birthdate": "1992-02-05",
        "position": "Forward",
        "current_club": "Al-Hilal"
    },
    {
        "name": "Robert Lewandowski",
        "slug": "lewandowski",
        "aliases": ["lewandowski", "robert lewandowski", "lewy"],
        "country": "Poland",
        "birthdate": "1988-08-21",
        "position": "Forward",
        "current_club": "Barcelona"
    },
    {
        "name": "Antoine Griezmann",
        "slug": "griezmann",
        "aliases": ["griezmann", "antoine griezmann"],
        "country": "France",
        "birthdate": "1991-03-21",
        "position": "Forward",
        "current_club": "Atlético Madrid"
    },
    {
        "name": "Luka Modrić",
        "slug": "modric",
        "aliases": ["modric", "luka modric"],
        "country": "Croatia",
        "birthdate": "1985-09-09",
        "position": "Midfielder",
        "current_club": "Real Madrid"
    },
    {
        "name": "Kai Havertz",
        "slug": "havertz",
        "aliases": ["havertz", "kai havertz"],
        "country": "Germany",
        "birthdate": "1999-06-11",
        "position": "Forward",
        "current_club": "Arsenal"
    },
    {
        "name": "Leroy Sané",
        "slug": "sane",
        "aliases": ["sane", "sané", "leroy sane", "leroy sané"],
        "country": "Germany",
        "birthdate": "1996-01-11",
        "position": "Forward",
        "current_club": "Bayern München"
    },
    {
        "name": "Joshua Kimmich",
        "slug": "kimmich",
        "aliases": ["kimmich", "joshua kimmich"],
        "country": "Germany",
        "birthdate": "1995-02-08",
        "position": "Midfielder",
        "current_club": "Bayern München"
    },
    {
        "name": "Niclas Füllkrug",
        "slug": "fuellkrug",
        "aliases": ["füllkrug", "fullkrug", "fuellkrug", "niclas füllkrug"],
        "country": "Germany",
        "birthdate": "1993-02-09",
        "position": "Forward",
        "current_club": "West Ham"
    },
    {
        "name": "Serge Gnabry",
        "slug": "gnabry",
        "aliases": ["gnabry", "serge gnabry"],
        "country": "Germany",
        "birthdate": "1995-07-14",
        "position": "Forward",
        "current_club": "Bayern München"
    },
    {
        "name": "İlkay Gündoğan",
        "slug": "gundogan",
        "aliases": ["gündogan", "gundogan", "ilkay gundogan"],
        "country": "Germany",
        "birthdate": "1990-10-24",
        "position": "Midfielder",
        "current_club": "Barcelona"
    },
]


async def seed_top_players():
    """Seed top players to database"""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    now = datetime.now(timezone.utc).isoformat()
    added = 0
    updated = 0
    
    for player_data in TOP_PLAYERS_DATA:
        # Check if player already exists
        existing = await db.players.find_one({"slug": player_data["slug"]})
        
        player_doc = {
            "name": player_data["name"],
            "slug": player_data["slug"],
            "aliases": player_data["aliases"],
            "country": player_data["country"],
            "birthdate": player_data["birthdate"],
            "position": player_data["position"],
            "image": None,
            "meta_title": f"{player_data['name']} Transfer-News | transfernews.de",
            "meta_description": f"Aktuelle Transfer-Gerüchte und News zu {player_data['name']}.",
            "updated_at": now
        }
        
        if existing:
            # Update existing player
            await db.players.update_one(
                {"slug": player_data["slug"]},
                {"$set": player_doc}
            )
            updated += 1
            print(f"Updated: {player_data['name']}")
        else:
            # Create new player
            player_doc["id"] = str(uuid.uuid4())
            player_doc["created_at"] = now
            await db.players.insert_one(player_doc)
            added += 1
            print(f"Added: {player_data['name']}")
    
    print(f"\nDone! Added: {added}, Updated: {updated}")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_top_players())
