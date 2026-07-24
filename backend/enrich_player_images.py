"""
Lädt Wikimedia-Bilder für die Top-Spieler in der Datenbank
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import aiohttp

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Wikimedia Commons API
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

# Bekannte gute Bilder für Top-Spieler (verifiziert)
KNOWN_GOOD_IMAGES = {
    "messi": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Lionel-Messi-Argentina-2022-FIFA-World-Cup_%28cropped%29.jpg/800px-Lionel-Messi-Argentina-2022-FIFA-World-Cup_%28cropped%29.jpg",
    "ronaldo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Cristiano_Ronaldo_2018.jpg/800px-Cristiano_Ronaldo_2018.jpg",
    "mbappe": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/2019-07-17_SG_Dynamo_Dresden_vs._Paris_Saint-Germain_by_Sandro_Halank%E2%80%93129_%28cropped%29.jpg/800px-2019-07-17_SG_Dynamo_Dresden_vs._Paris_Saint-Germain_by_Sandro_Halank%E2%80%93129_%28cropped%29.jpg",
    "haaland": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Erling_Haaland_2024.jpg/800px-Erling_Haaland_2024.jpg",
    "bellingham": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Jude_Bellingham_2024.jpg/800px-Jude_Bellingham_2024.jpg",
    "vinicius": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Vinicius_Junior_2024.jpg/800px-Vinicius_Junior_2024.jpg",
    "salah": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Mohamed_Salah_2018.jpg/800px-Mohamed_Salah_2018.jpg",
    "kane": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Harry_Kane_2024.jpg/800px-Harry_Kane_2024.jpg",
    "musiala": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Jamal_Musiala_2024.jpg/800px-Jamal_Musiala_2024.jpg",
    "wirtz": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Florian_Wirtz_2024.jpg/800px-Florian_Wirtz_2024.jpg",
    "saka": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Bukayo_Saka_2024.jpg/800px-Bukayo_Saka_2024.jpg",
    "palmer": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Cole_Palmer_2024.jpg/800px-Cole_Palmer_2024.jpg",
    "de-bruyne": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Kevin_De_Bruyne_201809091.jpg/800px-Kevin_De_Bruyne_201809091.jpg",
    "foden": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Phil_Foden_2024.jpg/800px-Phil_Foden_2024.jpg",
    "pedri": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Pedri_2024.jpg/800px-Pedri_2024.jpg",
    "neymar": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Neymar_vs_Lille.jpg/800px-Neymar_vs_Lille.jpg",
    "lewandowski": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Robert_Lewandowski%2C_FC_Bayern_M%C3%BCnchen_%28by_Sven_Mandel%2C_2019-05-27%29_02.jpg/800px-Robert_Lewandowski%2C_FC_Bayern_M%C3%BCnchen_%28by_Sven_Mandel%2C_2019-05-27%29_02.jpg",
    "griezmann": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Antoine_Griezmann_2018.jpg/800px-Antoine_Griezmann_2018.jpg",
    "modric": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/ISL-HRV_%287%29.jpg/800px-ISL-HRV_%287%29.jpg",
    "havertz": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fb/20180610_FIFA_Friendly_Match_Austria_vs._Brazil_Havertz_850_1705.jpg/800px-20180610_FIFA_Friendly_Match_Austria_vs._Brazil_Havertz_850_1705.jpg",
    "sane": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Leroy_Sane_2019.jpg/800px-Leroy_Sane_2019.jpg",
    "kimmich": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/20180602_FIFA_Friendly_Match_Austria_vs._Germany_Joshua_Kimmich_850_0703.jpg/800px-20180602_FIFA_Friendly_Match_Austria_vs._Germany_Joshua_Kimmich_850_0703.jpg",
    "fuellkrug": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Niclas_F%C3%BCllkrug_2024.jpg/800px-Niclas_F%C3%BCllkrug_2024.jpg",
    "gnabry": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/20180602_FIFA_Friendly_Match_Austria_vs._Germany_Serge_Gnabry_850_0693.jpg/800px-20180602_FIFA_Friendly_Match_Austria_vs._Germany_Serge_Gnabry_850_0693.jpg",
    "gundogan": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Ilkay_G%C3%BCndogan_2018.jpg/800px-Ilkay_G%C3%BCndogan_2018.jpg",
}


async def search_wikimedia_image(player_name: str) -> str:
    """Sucht ein Bild für einen Spieler auf Wikimedia Commons"""
    search_query = f"{player_name} football player portrait"
    
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": search_query,
        "gsrnamespace": "6",  # File namespace
        "gsrlimit": "5",
        "prop": "imageinfo",
        "iiprop": "url|size|mime",
        "iiurlwidth": "800"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(COMMONS_API, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    pages = data.get("query", {}).get("pages", {})
                    
                    for page_id, page in pages.items():
                        imageinfo = page.get("imageinfo", [{}])[0]
                        url = imageinfo.get("thumburl") or imageinfo.get("url")
                        mime = imageinfo.get("mime", "")
                        
                        if url and mime.startswith("image/"):
                            # Filtere Logos, Wappen, etc.
                            title_lower = page.get("title", "").lower()
                            if not any(bad in title_lower for bad in ["logo", "crest", "badge", "flag", "icon"]):
                                return url
    except Exception as e:
        print(f"Error searching for {player_name}: {e}")
    
    return None


async def verify_image_url(url: str) -> bool:
    """Prüft ob eine Bild-URL erreichbar ist"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=5, allow_redirects=True) as response:
                return response.status == 200
    except:
        return False


async def enrich_player_images():
    """Lädt Bilder für alle Top-Spieler"""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Hole alle Spieler ohne Bild
    players = await db.players.find(
        {"$or": [{"image": None}, {"image": ""}]},
        {"_id": 0, "id": 1, "name": 1, "slug": 1}
    ).to_list(100)
    
    print(f"Found {len(players)} players without images")
    
    updated = 0
    failed = []
    
    for player in players:
        slug = player["slug"]
        name = player["name"]
        
        # Erst bekannte gute Bilder prüfen
        image_url = KNOWN_GOOD_IMAGES.get(slug)
        
        if image_url:
            # Verifiziere URL
            if await verify_image_url(image_url):
                await db.players.update_one(
                    {"slug": slug},
                    {"$set": {"image": image_url}}
                )
                updated += 1
                print(f"✓ {name}: Known good image")
                continue
        
        # Sonst Wikimedia suchen
        image_url = await search_wikimedia_image(name)
        
        if image_url and await verify_image_url(image_url):
            await db.players.update_one(
                {"slug": slug},
                {"$set": {"image": image_url}}
            )
            updated += 1
            print(f"✓ {name}: Found via search")
        else:
            failed.append(name)
            print(f"✗ {name}: No image found")
        
        # Rate limiting
        await asyncio.sleep(0.5)
    
    print(f"\n=== Done ===")
    print(f"Updated: {updated}")
    print(f"Failed: {len(failed)}")
    if failed:
        print(f"Failed players: {', '.join(failed[:10])}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(enrich_player_images())
