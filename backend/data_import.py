"""
TransferNews.de - Data Import Services
- Football-Data.org API Integration
- News Scraper für Transfer-Meldungen
"""

import httpx
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import re
import hashlib
from typing import List, Dict, Optional
import logging
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from pymongo.errors import DuplicateKeyError
from pipeline_state import parse_source_time

logger = logging.getLogger(__name__)

# ============================================================================
# FOOTBALL-DATA.ORG API CLIENT
# ============================================================================

class FootballDataAPI:
    """
    Client für football-data.org API (Free Tier)
    Verfügbare Ligen: Bundesliga (BL1), Premier League (PL), La Liga (PD), 
    Serie A (SA), Ligue 1 (FL1), Champions League (CL), etc.
    """
    
    BASE_URL = "https://api.football-data.org/v4"
    
    # Wettbewerbs-IDs
    COMPETITIONS = {
        "bundesliga": "BL1",
        "premier-league": "PL", 
        "la-liga": "PD",
        "serie-a": "SA",
        "ligue-1": "FL1",
        "champions-league": "CL",
        "europa-league": "EL",
        "2-bundesliga": "BL2",
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"X-Auth-Token": api_key}
    
    async def _request(self, endpoint: str, params: dict = None) -> dict:
        """Make API request"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}{endpoint}",
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Football-Data API error: {e}")
                return {}
    
    async def get_competitions(self) -> List[dict]:
        """Get all available competitions"""
        data = await self._request("/competitions")
        return data.get("competitions", [])
    
    async def get_competition(self, competition_code: str) -> dict:
        """Get competition details"""
        return await self._request(f"/competitions/{competition_code}")
    
    async def get_teams(self, competition_code: str, season: int = None) -> List[dict]:
        """Get teams for a competition"""
        params = {}
        if season:
            params["season"] = season
        data = await self._request(f"/competitions/{competition_code}/teams", params)
        return data.get("teams", [])
    
    async def get_team(self, team_id: int) -> dict:
        """Get team details including squad"""
        return await self._request(f"/teams/{team_id}")
    
    async def get_scorers(self, competition_code: str, season: int = None, limit: int = 50) -> List[dict]:
        """Get top scorers (players) for a competition"""
        params = {"limit": limit}
        if season:
            params["season"] = season
        data = await self._request(f"/competitions/{competition_code}/scorers", params)
        return data.get("scorers", [])
    
    async def get_person(self, person_id: int) -> dict:
        """Get person/player details"""
        return await self._request(f"/persons/{person_id}")


def generate_slug(text: str) -> str:
    """Generate URL-friendly slug"""
    slug = text.lower()
    slug = re.sub(r'[äÄ]', 'ae', slug)
    slug = re.sub(r'[öÖ]', 'oe', slug)
    slug = re.sub(r'[üÜ]', 'ue', slug)
    slug = re.sub(r'[ß]', 'ss', slug)
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


async def import_competition_data(api: FootballDataAPI, competition_code: str, db) -> dict:
    """
    Import complete competition data: Competition, Teams, Players
    Returns summary of imported data
    """
    from models import Competition, Club, Player, generate_uuid
    
    result = {"competition": None, "clubs": 0, "players": 0}
    
    # 1. Import Competition
    comp_data = await api.get_competition(competition_code)
    if not comp_data:
        return result
    
    comp = Competition(
        id=generate_uuid(),
        name=comp_data.get("name", ""),
        slug=generate_slug(comp_data.get("name", "")),
        country=comp_data.get("area", {}).get("name"),
        type="league" if "league" in comp_data.get("type", "").lower() else "cup",
        logo=comp_data.get("emblem"),
    )
    
    # Check if exists
    existing = await db.competitions.find_one({"slug": comp.slug})
    if not existing:
        await db.competitions.insert_one(comp.model_dump())
        result["competition"] = comp.name
    else:
        comp.id = existing["id"]
        result["competition"] = f"{comp.name} (existiert)"
    
    # 2. Import Teams
    teams = await api.get_teams(competition_code)
    for team_data in teams:
        club = Club(
            id=generate_uuid(),
            name=team_data.get("name", ""),
            slug=generate_slug(team_data.get("name", "")),
            country=team_data.get("area", {}).get("name"),
            competition_id=comp.id,
            logo=team_data.get("crest"),
            aliases=[team_data.get("shortName", ""), team_data.get("tla", "")],
        )
        club.aliases = [a for a in club.aliases if a]  # Remove empty
        
        existing_club = await db.clubs.find_one({"slug": club.slug})
        if not existing_club:
            await db.clubs.insert_one(club.model_dump())
            result["clubs"] += 1
            
            # 3. Import Players from squad
            team_details = await api.get_team(team_data.get("id"))
            squad = team_details.get("squad", [])
            
            for player_data in squad:
                player = Player(
                    id=generate_uuid(),
                    name=player_data.get("name", ""),
                    slug=generate_slug(player_data.get("name", "")),
                    country=player_data.get("nationality"),
                    birthdate=player_data.get("dateOfBirth"),
                    position=player_data.get("position"),
                    current_club_id=club.id,
                )
                
                existing_player = await db.players.find_one({"slug": player.slug})
                if not existing_player:
                    await db.players.insert_one(player.model_dump())
                    result["players"] += 1
    
    return result


# ============================================================================
# NEWS SCRAPER
# ============================================================================

class TransferNewsScraper:
    """
    Scraper für Transfer-News von deutschen und internationalen Quellen
    """
    
    SOURCES = {
        "sky_sport_de": {
            "url": "https://sport.sky.de/fussball/transfermarkt",
            "name": "Sky Sport DE",
            "type": "media",
            "category": "tier_1",
        },
        "kicker": {
            "url": "https://www.kicker.de/transfergeruechte",
            "name": "Kicker",
            "type": "media", 
            "category": "tier_1",
        },
        "sport1": {
            "url": "https://www.sport1.de/fussball/transfermarkt",
            "name": "Sport1",
            "type": "media",
            "category": "tier_2",
        },
        "transfermarkt_news": {
            "url": "https://www.transfermarkt.de/transfers/transferticker/statistik",
            "name": "Transfermarkt",
            "type": "official",
            "category": "tier_1",
        },
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    }
    
    def __init__(self):
        self.client = httpx.AsyncClient(headers=self.HEADERS, timeout=30, follow_redirects=True)
    
    async def close(self):
        await self.client.aclose()
    
    def _generate_dedupe_key(self, headline: str, source: str) -> str:
        """Generate unique key for deduplication"""
        content = f"{headline.lower()[:100]}:{source}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def scrape_sky_sport_de(self) -> List[dict]:
        """Scrape Sky Sport DE Transfer News"""
        events = []
        try:
            response = await self.client.get(self.SOURCES["sky_sport_de"]["url"])
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find news articles
            articles = soup.find_all("article") or soup.find_all("div", class_=re.compile(r"news|article|teaser", re.I))
            
            for article in articles[:15]:
                headline_elem = article.find(["h2", "h3", "h4", "a"])
                if headline_elem:
                    headline = headline_elem.get_text(strip=True)
                    if len(headline) > 20 and any(kw in headline.lower() for kw in ["transfer", "wechsel", "interesse", "ablöse", "verhandl", "verpflicht"]):
                        link = headline_elem.get("href", "")
                        if link and not link.startswith("http"):
                            link = "https://sport.sky.de" + link
                        
                        events.append({
                            "headline_raw": headline,
                            "source_url": link,
                            "source_key": "sky_sport_de",
                            "dedupe_key": self._generate_dedupe_key(headline, "sky"),
                        })
        except Exception as e:
            logger.error(f"Sky Sport scrape error: {e}")
        
        return events
    
    async def scrape_kicker(self) -> List[dict]:
        """Scrape Kicker Transfer-Gerüchte"""
        events = []
        try:
            response = await self.client.get(self.SOURCES["kicker"]["url"])
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find transfer items
            items = soup.find_all("div", class_=re.compile(r"teaser|article|news", re.I))
            
            for item in items[:15]:
                headline_elem = item.find(["h2", "h3", "h4"])
                if headline_elem:
                    headline = headline_elem.get_text(strip=True)
                    if len(headline) > 15:
                        link_elem = item.find("a", href=True)
                        link = ""
                        if link_elem:
                            link = link_elem["href"]
                            if not link.startswith("http"):
                                link = "https://www.kicker.de" + link
                        
                        events.append({
                            "headline_raw": headline,
                            "source_url": link,
                            "source_key": "kicker",
                            "dedupe_key": self._generate_dedupe_key(headline, "kicker"),
                        })
        except Exception as e:
            logger.error(f"Kicker scrape error: {e}")
        
        return events
    
    async def scrape_sport1(self) -> List[dict]:
        """Scrape Sport1 Transfermarkt"""
        events = []
        try:
            response = await self.client.get(self.SOURCES["sport1"]["url"])
            soup = BeautifulSoup(response.content, "html.parser")
            
            articles = soup.find_all(["article", "div"], class_=re.compile(r"article|teaser|card", re.I))
            
            for article in articles[:15]:
                headline_elem = article.find(["h2", "h3", "h4", "span"], class_=re.compile(r"title|headline", re.I))
                if headline_elem:
                    headline = headline_elem.get_text(strip=True)
                    if len(headline) > 15:
                        link_elem = article.find("a", href=True)
                        link = link_elem["href"] if link_elem else ""
                        if link and not link.startswith("http"):
                            link = "https://www.sport1.de" + link
                        
                        events.append({
                            "headline_raw": headline,
                            "source_url": link,
                            "source_key": "sport1",
                            "dedupe_key": self._generate_dedupe_key(headline, "sport1"),
                        })
        except Exception as e:
            logger.error(f"Sport1 scrape error: {e}")
        
        return events
    
    async def scrape_all(self) -> List[dict]:
        """Scrape all sources"""
        all_events = []
        
        # Run scrapers in parallel
        results = await asyncio.gather(
            self.scrape_sky_sport_de(),
            self.scrape_kicker(),
            self.scrape_sport1(),
            return_exceptions=True
        )
        
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraper error: {result}")
        
        return all_events


async def import_scraped_events(scraper: TransferNewsScraper, db) -> dict:
    """
    Import scraped events into database
    Returns summary of imported events
    """
    from models import Event, Source, EventType, EventStatus, SourceType, SourceCategory, generate_uuid
    
    result = {"new_events": 0, "duplicates": 0, "sources_created": 0}
    
    # Ensure sources exist
    for source_key, source_info in scraper.SOURCES.items():
        existing = await db.sources.find_one({"slug": source_key})
        if not existing:
            source = Source(
                id=generate_uuid(),
                name=source_info["name"],
                slug=source_key,
                type=SourceType(source_info["type"]),
                source_url=source_info["url"],
                source_category=SourceCategory(source_info["category"]),
                active=True,
                trust_score=80 if source_info["category"] == "tier_1" else 60,
            )
            await db.sources.insert_one(source.model_dump())
            result["sources_created"] += 1
    
    # Scrape all sources
    events = await scraper.scrape_all()
    
    # Import events
    for event_data in events:
        # Check for duplicate
        existing = await db.events.find_one({"$or": [
            {"dedupe_key": event_data["dedupe_key"]},
            {"dedupe_key": event_data.get("legacy_dedupe_key", event_data["dedupe_key"]), "headline_raw": event_data["headline_raw"]}
        ]})
        if existing:
            result["duplicates"] += 1
            continue
        
        # Get source ID
        source = await db.sources.find_one({"slug": event_data["source_key"]})
        source_id = source["id"] if source else None
        
        # Determine event type based on keywords
        headline_lower = event_data["headline_raw"].lower()
        if any(kw in headline_lower for kw in ["offiziell", "bestätigt", "fix", "unterschrieben"]):
            event_type = EventType.OFFICIAL
        elif any(kw in headline_lower for kw in ["einigung", "agreement", "deal"]):
            event_type = EventType.CONFIRMED
        elif any(kw in headline_lower for kw in ["kurz vor", "verhandlung", "gespräch"]):
            event_type = EventType.ADVANCED
        else:
            event_type = EventType.RUMOUR
        
        event = Event(
            id=generate_uuid(),
            event_type=event_type,
            status=EventStatus.PENDING,
            headline_raw=event_data["headline_raw"],
            body_raw=event_data.get("summary", ""),
            source_published_at=event_data.get("source_published_at"),
            source_id=source_id,
            source_url=event_data.get("source_url", ""),
            dedupe_key=event_data["dedupe_key"],
            confidence_score=70 if event_type in [EventType.OFFICIAL, EventType.CONFIRMED] else 50,
        )
        
        await db.events.insert_one(event.model_dump())
        result["new_events"] += 1
    
    return result


# ============================================================================
# LLM ARTICLE GENERATOR
# ============================================================================

import os


def extract_player_names(title: str) -> List[str]:
    """
    Extract potential player names from article title
    Returns list of potential player names
    """
    import re
    
    # Known football player names (extended list)
    known_players = {
        "sancho": "Jadon Sancho",
        "olise": "Michael Olise",
        "rodri": "Rodri",
        "salah": "Mohamed Salah",
        "mbappe": "Kylian Mbappe",
        "haaland": "Erling Haaland",
        "bellingham": "Jude Bellingham",
        "kane": "Harry Kane",
        "lewandowski": "Robert Lewandowski",
        "messi": "Lionel Messi",
        "ronaldo": "Cristiano Ronaldo",
        "neymar": "Neymar Jr",
        "vinicius": "Vinicius Junior",
        "rashford": "Marcus Rashford",
        "musiala": "Jamal Musiala",
        "wirtz": "Florian Wirtz",
        "kimmich": "Joshua Kimmich",
        "gnabry": "Serge Gnabry",
        "sane": "Leroy Sane",
        "havertz": "Kai Havertz",
        "werner": "Timo Werner",
        "muller": "Thomas Muller",
        "neuer": "Manuel Neuer",
        "ter stegen": "Marc-Andre ter Stegen",
        "de bruyne": "Kevin de Bruyne",
        "gundogan": "Ilkay Gundogan",
        "nagelsmann": "Julian Nagelsmann",
        "schlotterbeck": "Nico Schlotterbeck",
        "saka": "Bukayo Saka",
        "rice": "Declan Rice",
        "odegaard": "Martin Odegaard",
        "palmer": "Cole Palmer",
        "arnold": "Alexander-Arnold",
        "dahoud": "Mahmoud Dahoud",
        "larsson": "Hugo Larsson",
        "griezmann": "Antoine Griezmann",
        "casemiro": "Casemiro",
        "modric": "Luka Modric",
        "kroos": "Toni Kroos",
    }
    
    # Club name patterns to exclude
    club_patterns = [
        "fc", "bayern", "dortmund", "liverpool", "madrid", "barcelona", 
        "manchester", "chelsea", "arsenal", "city", "united", "psg",
        "juventus", "inter", "milan", "roma", "napoli", "atletico",
        "bvb", "frankfurt", "leverkusen", "schalke", "bremen", "köln"
    ]
    
    # German words to exclude
    exclude_words = [
        "transfer", "wechsel", "verlässt", "kommt", "geht", "bleibt",
        "verhandelt", "rückkehr", "abgang", "zugang", "interesse",
        "ablöse", "vertrag", "million", "euro", "saison", "sommer",
        "winter", "star", "spieler", "trainer", "manager", "deal"
    ]
    
    title_lower = title.lower()
    potential_names = []
    
    # First: Check for known player names
    for key, full_name in known_players.items():
        if key in title_lower:
            potential_names.append(full_name)
    
    # If known players found, return them first
    if potential_names:
        return potential_names[:3]
    
    # Otherwise: Extract capitalized words that could be names
    words = title.split()
    
    i = 0
    while i < len(words):
        word = words[i]
        # Clean the word - remove hyphens and special chars
        clean_word = re.sub(r'[^\w]', '', word.split('-')[0])
        
        # Skip short words or known patterns
        if len(clean_word) < 4:
            i += 1
            continue
            
        if clean_word.lower() in club_patterns or clean_word.lower() in exclude_words:
            i += 1
            continue
        
        # Check if it starts with uppercase (potential name)
        if clean_word and clean_word[0].isupper():
            # Check for full name (First Last)
            if i + 1 < len(words):
                next_word = re.sub(r'[^\w]', '', words[i + 1].split('-')[0])
                if (next_word and len(next_word) >= 3 and 
                    next_word[0].isupper() and 
                    next_word.lower() not in club_patterns and
                    next_word.lower() not in exclude_words):
                    full_name = f"{clean_word} {next_word}"
                    potential_names.append(full_name)
                    i += 2
                    continue
            
            # Single name (at least 5 chars to be a potential player name)
            if len(clean_word) >= 5:
                potential_names.append(clean_word)
        
        i += 1
    
    return potential_names[:3]  # Max 3 names


async def search_player_image_unsplash(player_name: str) -> str:
    """
    Search for player image using Unsplash API
    Returns image URL if found
    """
    import random
    
    # Clean player name for search
    search_query = f"{player_name} football soccer"
    search_query = search_query.replace(" ", ",")
    
    # Use Unsplash Source (free, no API key)
    rand = random.randint(1, 10000)
    return f"https://source.unsplash.com/800x600/?{search_query}&sig={rand}"


async def scrape_player_image_from_sports_sites(player_name: str) -> str:
    """
    Scrape player images from international sports websites.
    Priority: Player name search on ESPN, Sky Sports, Goal.com, etc.
    """
    import aiohttp
    from bs4 import BeautifulSoup
    from urllib.parse import quote
    
    # International sports sites to scrape (non-German)
    SPORTS_SITES = [
        {
            "name": "ESPN",
            "search_url": "https://www.espn.com/search/_/q/{query}",
            "base_url": "https://www.espn.com",
            "img_selector": "img.Image",
        },
        {
            "name": "Sky Sports",
            "search_url": "https://www.skysports.com/search?q={query}",
            "base_url": "https://www.skysports.com",
            "img_selector": "img",
        },
        {
            "name": "Goal.com",
            "search_url": "https://www.goal.com/en/search?q={query}",
            "base_url": "https://www.goal.com",
            "img_selector": "img",
        },
        {
            "name": "Transfermarkt UK",
            "search_url": "https://www.transfermarkt.co.uk/schnellsuche/ergebnis/schnellsuche?query={query}",
            "base_url": "https://www.transfermarkt.co.uk",
            "img_selector": "img.bilderrahmen-fixed",
        },
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    query = quote(player_name)
    
    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
        for site in SPORTS_SITES:
            try:
                url = site["search_url"].format(query=query)
                logger.info(f"Searching {site['name']} for: {player_name}")
                
                async with session.get(url) as response:
                    if response.status != 200:
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # Find images
                    images = soup.find_all("img")
                    
                    for img in images:
                        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                        if not src:
                            continue
                        
                        # Filter: Must be a decent sized image, likely a player photo
                        # Skip tiny icons, logos, etc.
                        width = img.get("width", "0")
                        height = img.get("height", "0")
                        
                        try:
                            w = int(str(width).replace("px", "")) if width else 0
                            h = int(str(height).replace("px", "")) if height else 0
                        except:
                            w, h = 0, 0
                        
                        # Check if image URL looks like a player photo
                        src_lower = src.lower()
                        
                        # Skip common non-player images
                        skip_patterns = ["logo", "icon", "sprite", "banner", "ad", "tracking", "pixel", "badge", "flag"]
                        if any(p in src_lower for p in skip_patterns):
                            continue
                        
                        # Prefer images that look like player photos
                        good_patterns = ["player", "headshot", "portrait", "foto", "photo", "bild", "image"]
                        is_likely_player = any(p in src_lower for p in good_patterns)
                        
                        # Accept if large enough or looks like player photo
                        if (w >= 100 and h >= 100) or is_likely_player or ("jpg" in src_lower or "jpeg" in src_lower or "png" in src_lower):
                            # Make absolute URL
                            if src.startswith("//"):
                                src = "https:" + src
                            elif src.startswith("/"):
                                src = site["base_url"] + src
                            elif not src.startswith("http"):
                                continue
                            
                            # Skip data URIs
                            if src.startswith("data:"):
                                continue
                            
                            logger.info(f"Found image on {site['name']}: {src[:80]}...")
                            return src
                            
            except Exception as e:
                logger.warning(f"Error scraping {site['name']}: {e}")
                continue
    
    return ""


async def scrape_player_image_bing(player_name: str) -> str:
    """
    Search for player image using Bing Images (no API key needed)
    """
    import aiohttp
    from bs4 import BeautifulSoup
    from urllib.parse import quote
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    query = quote(f"{player_name} football player")
    url = f"https://www.bing.com/images/search?q={query}&form=HDRSC2&first=1"
    
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return ""
                
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                
                # Find image thumbnails
                images = soup.find_all("img", class_="mimg")
                
                for img in images[:5]:
                    src = img.get("src") or img.get("data-src")
                    if src and src.startswith("http") and "bing" not in src.lower():
                        logger.info(f"Found Bing image: {src[:60]}...")
                        return src
                
                # Alternative: Find in a tags
                links = soup.find_all("a", class_="iusc")
                for link in links[:5]:
                    m = link.get("m")
                    if m:
                        import json
                        try:
                            data = json.loads(m)
                            if "murl" in data:
                                logger.info(f"Found Bing murl: {data['murl'][:60]}...")
                                return data["murl"]
                        except:
                            pass
                            
    except Exception as e:
        logger.warning(f"Bing search error: {e}")
    
    return ""


async def search_player_image_pexels(player_name: str) -> str:
    """
    Search for player image using Pexels API
    Falls back to generic football if no results
    """
    import os
    import aiohttp
    
    # Pexels requires API key - skip if not available
    pexels_key = os.environ.get("PEXELS_API_KEY", "")
    if not pexels_key:
        return ""
    
    try:
        search_query = f"{player_name} football"
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": pexels_key}
            url = f"https://api.pexels.com/v1/search?query={search_query}&per_page=1"
            
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    photos = data.get("photos", [])
                    if photos:
                        return photos[0].get("src", {}).get("large", "")
    except Exception as e:
        logger.error(f"Pexels search error: {e}")
    
    return ""


async def find_best_player_image(title: str, article_id: str) -> str:
    """
    Find the best available image for an article
    Priority:
    1. Scrape from international sports sites (ESPN, Sky Sports, Goal, Transfermarkt UK)
    2. Bing Image Search
    3. Fallback to generic football image
    """
    
    # Extract player names from title
    player_names = extract_player_names(title)
    
    # Try to find image for each player name
    for player_name in player_names:
        logger.info(f"Searching image for player: {player_name}")
        
        # Priority 1: Scrape from international sports sites
        image_url = await scrape_player_image_from_sports_sites(player_name)
        if image_url:
            saved_path = await download_and_save_image(image_url, article_id)
            if saved_path:
                logger.info(f"Found sports site image for: {player_name}")
                return saved_path
        
        # Priority 2: Bing Image Search
        image_url = await scrape_player_image_bing(player_name)
        if image_url:
            saved_path = await download_and_save_image(image_url, article_id)
            if saved_path:
                logger.info(f"Found Bing image for: {player_name}")
                return saved_path
    
    # Fallback: generic football image from Unsplash
    title_lower = title.lower()
    keyword_map = {
        "bayern": "bayern munich stadium",
        "dortmund": "dortmund football",
        "liverpool": "liverpool football",
        "real madrid": "real madrid stadium",
        "barcelona": "barcelona football",
        "manchester": "manchester football",
        "chelsea": "chelsea football",
        "arsenal": "arsenal football",
        "bundesliga": "bundesliga football",
        "premier league": "premier league football",
        "champions league": "champions league football",
    }
    
    for keyword, search_term in keyword_map.items():
        if keyword in title_lower:
            import random
            rand = random.randint(1, 10000)
            url = f"https://source.unsplash.com/800x600/?{search_term.replace(' ', ',')}&sig={rand}"
            saved_path = await download_and_save_image(url, article_id)
            if saved_path:
                return saved_path
    
    # Last resort: generic football
    return await download_fallback_image(article_id, "football,soccer,stadium")


async def find_related_events(db, event: dict, limit: int = 5) -> List[dict]:
    """Find related events about the same topic from different sources"""
    headline = event.get("headline_raw", "").lower()
    
    # Extract key entities (player names, club names)
    words = headline.split()
    key_terms = [w for w in words if len(w) > 4 and w[0].isupper()]
    
    if not key_terms:
        return [event]
    
    # Search for related events
    related = []
    for term in key_terms[:3]:
        cursor = db.events.find({
            "headline_raw": {"$regex": term, "$options": "i"},
            "id": {"$ne": event.get("id")}
        }).limit(limit)
        async for e in cursor:
            if e not in related:
                related.append(e)
    
    return [event] + related[:4]  # Max 5 sources


async def generate_article_from_event(event: dict, db) -> dict:
    """Compatibility entry point; all publication goes through the guarded pipeline."""
    from speed_pipeline import SpeedPipeline
    outcome = await SpeedPipeline(db).process_event(event)
    if not outcome.get("article_id"):
        raise ValueError(outcome.get("reason", "event_requires_review"))
    return await db.articles.find_one({"id": outcome["article_id"]}, {"_id": 0})


async def process_pending_events(db, limit: int = 5) -> dict:
    """Legacy admin actions share the same lease, freshness and retry protections."""
    from speed_pipeline import SpeedPipeline
    result = await SpeedPipeline(db).process_pending_events(limit)
    return {**result, "articles_created": result.get("created", 0), "articles_updated": result.get("updated", 0)}


async def find_existing_article_for_event(db, event: dict) -> dict:
    """
    Find if an article already exists for this transfer event
    Checks player names, clubs, and recent publication date
    """
    from datetime import timedelta
    
    headline = event.get("headline_raw", "")
    
    # Extract key entities from headline
    player_names = extract_player_names(headline)
    
    if not player_names:
        return None
    
    # Search for existing articles from last 7 days
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    
    for player in player_names:
        # Check if article with this player exists
        query = {
            "status": "published",
            "published_at": {"$gte": cutoff},
            "$or": [
                {"title": {"$regex": player, "$options": "i"}},
                {"body": {"$regex": player, "$options": "i"}}
            ]
        }
        
        existing = await db.articles.find_one(query, {"_id": 0})
        if existing:
            return existing
    
    return None


async def update_existing_article(db, article: dict, new_event: dict) -> None:
    """
    Update existing article with new information from event
    - Updates status if event has higher confidence
    - Appends new information to body
    - Updates timestamp
    """
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Determine new status based on event type
    event_type = new_event.get("event_type", "rumour").lower()
    current_status = article.get("transfer_status", "rumour")
    
    status_priority = {"rumour": 1, "advanced": 2, "confirmed": 3, "official": 4}
    
    new_status = current_status
    if status_priority.get(event_type, 0) > status_priority.get(current_status, 0):
        new_status = event_type
    
    # Build update paragraph
    status_labels = {
        "rumour": "Gerücht",
        "advanced": "Fortgeschritten",
        "confirmed": "Bestätigt", 
        "official": "Offiziell"
    }
    
    update_text = new_event.get("headline_raw", "")
    source_url = new_event.get("source_url", "")
    
    update_paragraph = f"\n\n**UPDATE ({status_labels.get(new_status, 'Neu')}):** {update_text}"
    
    # Update probability based on status
    probability_map = {
        "rumour": 25,
        "advanced": 60,
        "confirmed": 85,
        "official": 100
    }
    
    update_data = {
        "transfer_status": new_status,
        "updated_at": now,
        "body": article.get("body", "") + update_paragraph
    }
    
    if new_status in probability_map:
        update_data["transfer_probability"] = probability_map[new_status]
    
    await db.articles.update_one(
        {"id": article["id"]},
        {"$set": update_data}
    )


# ============================================================================
# RSS FEED SCRAPER (More reliable than HTML scraping)
# ============================================================================

import feedparser

class RSSFeedScraper:
    """
    RSS Feed Scraper für Transfer-News
    Internationale + Deutsche Quellen mit automatischer Übersetzung
    """
    
    FEEDS = {
        # =============================================
        # 🌍 GLOBAL SOURCES (Priority 1 - Instant)
        # =============================================
        "caughtoffside": {
            "url": "https://www.caughtoffside.com/feed/",
            "name": "CaughtOffside",
            "category": "tier_1",
            "language": "en",
            "trust_score": 85,
            "region": "global",
            "speed": "fast",
        },
        "90min": {
            "url": "https://www.90min.com/posts.rss",
            "name": "90min",
            "category": "tier_1",
            "language": "en",
            "trust_score": 82,
            "region": "global",
            "speed": "fast",
        },
        "footballtransfers": {
            "url": "https://www.footballtransfers.com/en/feed",
            "name": "FootballTransfers",
            "category": "tier_2",
            "language": "en",
            "trust_score": 88,
            "region": "global",
            "speed": "medium",
        },
        "goal_com": {
            "url": "https://www.goal.com/feeds/en/news",
            "name": "Goal",
            "category": "tier_2",
            "language": "en",
            "trust_score": 80,
            "region": "global",
            "speed": "medium",
        },
        
        # =============================================
        # 🇬🇧 UK SOURCES (Premier League Dominanz)
        # =============================================
        "sky_sports_uk": {
            "url": "https://www.skysports.com/rss/11095",
            "name": "Sky Sports",
            "category": "tier_1",
            "language": "en",
            "trust_score": 95,
            "region": "uk",
            "speed": "very_fast",
        },
        "bbc_football": {
            "url": "http://feeds.bbci.co.uk/sport/football/rss.xml",
            "name": "BBC Sport",
            "category": "tier_2",
            "language": "en",
            "trust_score": 92,
            "region": "uk",
            "speed": "medium",
        },
        "teamtalk": {
            "url": "https://www.teamtalk.com/feed",
            "name": "TEAMtalk",
            "category": "tier_2",
            "language": "en",
            "trust_score": 78,
            "region": "uk",
            "speed": "fast",
        },
        
        # =============================================
        # 🇪🇸 SPAIN SOURCES (La Liga + Südamerika)
        # =============================================
        "marca": {
            # Current official LaLiga feed; historical all-football feed is stale.
            "url": "https://objetos.estaticos-marca.com/rss/futbol/primera-division.xml",
            "name": "Marca",
            "category": "tier_1",
            "language": "es",
            "trust_score": 90,
            "region": "spain",
            "speed": "very_fast",
        },
        "as_spain": {
            "url": "https://as.com/rss/tags/ultimas_noticias.xml",
            "name": "AS",
            "category": "tier_2",
            "language": "es",
            "trust_score": 85,
            "region": "spain",
            "speed": "fast",
        },
        "mundo_deportivo": {
            "url": "https://www.mundodeportivo.com/rss/futbol.xml",
            "name": "Mundo Deportivo",
            "category": "tier_2",
            "language": "es",
            "trust_score": 83,
            "region": "spain",
            "speed": "fast",
        },
        
        # =============================================
        # 🇮🇹 ITALY SOURCES (Serie A Leak Zone)
        # =============================================
        "gazzetta": {
            "url": "https://www.gazzetta.it/dynamic-feed/rss/section/Calcio.xml",
            "name": "Gazzetta dello Sport",
            "category": "tier_1",
            "language": "it",
            "trust_score": 88,
            "region": "italy",
            "speed": "very_fast",
        },
        "corriere_sport": {
            "url": "https://www.corrieredellosport.it/rss/home.xml",
            "name": "Corriere dello Sport",
            "category": "tier_2",
            "language": "it",
            "trust_score": 82,
            "region": "italy",
            "speed": "fast",
        },
        "tuttosport": {
            "url": "https://www.tuttosport.com/rss/home.xml",
            "name": "Tuttosport",
            "category": "tier_2",
            "language": "it",
            "trust_score": 80,
            "region": "italy",
            "speed": "fast",
        },
        
        # =============================================
        # 🇫🇷 FRANCE SOURCES (PSG + Talents)
        # =============================================
        "lequipe": {
            "url": "https://www.lequipe.fr/rss/actu_rss_Football.xml",
            "name": "L'Équipe",
            "category": "tier_1",
            "language": "fr",
            "trust_score": 90,
            "region": "france",
            "speed": "very_fast",
        },
        "rmc_sport": {
            "url": "https://rmcsport.bfmtv.com/rss/football/",
            "name": "RMC Sport",
            "category": "tier_2",
            "language": "fr",
            "trust_score": 82,
            "region": "france",
            "speed": "fast",
        },
        "foot_mercato": {
            "url": "https://www.footmercato.net/flux-rss",
            "name": "Foot Mercato",
            "category": "tier_2",
            "language": "fr",
            "trust_score": 85,
            "region": "france",
            "speed": "fast",
        },
        
        # =============================================
        # 🇩🇪 GERMANY SOURCES (Bundesliga)
        # =============================================
        "bild_fussball": {
            "url": "https://www.bild.de/feed/sport.xml",
            "allowed_hosts": ["www.bild.de", "bild.de"],
            "allowed_path_prefixes": ["/sport/fussball/"],
            "name": "BILD",
            "category": "tier_1",
            "language": "de",
            "trust_score": 85,
            "region": "germany",
            "speed": "very_fast",
        },
        "kicker": {
            "url": "https://newsfeed.kicker.de/news/aktuell",
            "name": "kicker",
            "category": "tier_2",
            "language": "de",
            "trust_score": 90,
            "region": "germany",
            "speed": "medium",
        },
        "sport1": {
            "url": "https://www.sport1.de/rss/news",
            "name": "Sport1",
            "category": "tier_2",
            "language": "de",
            "trust_score": 82,
            "region": "germany",
            "speed": "fast",
        },
    }
    
    # Retain source keys/configuration and database history. Disabled sources are
    # reported separately from transient fetch errors, never silently retried.
    DISABLED_FEEDS = {
        "lequipe": {"reason": "blocked_403", "checked_on": "2026-09-20"},
        "sport1": {"reason": "official_feed_blocked_403", "checked_on": "2026-09-20",
                   "official_feed_url": "https://www.sport1.de/feed"},
        "teamtalk": {"reason": "feed_404_no_verified_replacement", "checked_on": "2026-09-20"},
        "goal_com": {"reason": "feed_404_no_verified_replacement", "checked_on": "2026-09-20"},
        "footballtransfers": {"reason": "html_instead_of_feed", "checked_on": "2026-09-20"},
    }

    @classmethod
    def active_feeds(cls):
        return {key: info for key, info in cls.FEEDS.items() if key not in cls.DISABLED_FEEDS}

    @staticmethod
    def _entry_in_scope(info, link):
        hosts = info.get("allowed_hosts")
        prefixes = info.get("allowed_path_prefixes")
        if not hosts and not prefixes:
            return True
        try:
            parsed = urlsplit(link)
            if parsed.scheme not in {"http", "https"}:
                return False
            if hosts and parsed.netloc.casefold() not in hosts:
                return False
            return not prefixes or any(parsed.path.startswith(prefix) for prefix in prefixes)
        except (TypeError, ValueError):
            return False

    # Transfer keywords für verschiedene Sprachen (erweitert)
    TRANSFER_KEYWORDS = {
        "de": [
            "transfer", "verpflichtet", "verpflichtung",
            "wechselt zu", "wechselt von", "wechsel zu", "wechsel von",
            "ablöse", "ablösefrei", "ablösesumme",
            "unterschreibt bei", "unterschrieben bei", "vertrag unterschrieben",
            "leihe von", "leihe zu", "leihgeschäft", "ausgeliehen",
            "verkauft", "gekauft", "transfer-", "transfersumme",
            "kommt von", "geht zu", "verlässt den",
            "neuzugang", "abgang", "rückkehr zu", "medizincheck"
        ],
        "en": [
            "transfer", "signs for", "signed for", "signing",
            "joins", "joining", "deal", "move to", "moves to",
            "loan", "loaned", "fee", "bid", "offer",
            "completes move", "agrees terms", "personal terms",
            "medical", "here we go", "done deal", "confirmed",
            "targets", "interested in", "pursuing", "chase",
            "release clause", "contract", "extension", "agreement"
        ],
        "es": [
            "fichaje", "ficha por", "contrato", "cesión",
            "traspaso", "acuerdo", "cierre", "llega a",
            "se marcha", "renovación", "firma", "oficial",
            "préstamo", "cláusula", "millones"
        ],
        "it": [
            "trasferimento", "affare", "accordo", "contratto",
            "prestito", "cessione", "ufficiale", "firma",
            "clausola", "milioni", "arriva", "va via"
        ],
        "fr": [
            "transfert", "prêt", "signature", "accord",
            "contrat", "officiel", "rejoint", "quitte",
            "clause", "millions", "mercato"
        ],
    }
    
    # Priority Handling für Speed-Kategorien
    PRIORITY_SPEED = {
        "very_fast": 0,   # Sofortige Verarbeitung
        "fast": 1,        # Priorität 1
        "medium": 2,      # Priorität 2
    }
    
    def _generate_dedupe_key(self, title: str, source: str, url: str = "", summary: str = "") -> str:
        parts = urlsplit(url)
        canonical = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path,
            urlencode(sorted((key, value) for key, value in parse_qsl(parts.query) if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid"})), ""))
        content = "\n".join([source, canonical, " ".join(title.casefold().split()), " ".join(summary.split())])
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _is_transfer_related(self, title: str, summary: str = "", language: str = "de") -> bool:
        """
        Check if article is a real TRANSFER news
        Supports multiple languages (de, en, es)
        """
        text = f"{title} {summary}".lower()
        
        # EXCLUDE non-transfer news (multilingual)
        exclude_terms = [
            # German
            "testspiel", "auswechslung", "einwechslung", "spieltag",
            "tor geschossen", "torschütze", "ergebnis", "endergebnis",
            "halbzeit", "anpfiff", "abpfiff", "elfmeter", "freistoß",
            "rote karte", "gelbe karte", "verletzung", "verletzt",
            "marktwert", "marktwerte", "ranking", "statistik",
            "interview", "pressekonferenz", "pk",
            # English
            "match report", "goal scored", "red card", "yellow card",
            "injury update", "lineup", "starting xi", "preview",
            "highlights", "recap", "results", "fixtures", "standings",
            "press conference", "interview", "quotes",
            "play-off", "playoffs", "semi-final", "quarter-final",
            "champions league draw", "europa league draw",
            # Sports that are NOT football
            "rugby", "cricket", "tennis", "golf", "f1", "formula 1",
            "nfl", "nba", "nhl", "mlb", "boxing", "mma", "ufc",
            "harlequins", "saracens", "northampton", "bristol bears",
            # Spanish
            "lesión", "tarjeta roja", "tarjeta amarilla", "goles"
        ]
        
        other_sports = ["rugby", "cricket", "tennis", "golf", "formula 1", "nfl", "nba", "nhl", "mlb", "boxing", "mma", "ufc"]
        if any(re.search(r"\b" + re.escape(term) + r"\b", text) for term in other_sports):
            return False
        
        # Get keywords for language (fallback to all languages)
        all_keywords = []
        for lang_keywords in self.TRANSFER_KEYWORDS.values():
            all_keywords.extend(lang_keywords)
        
        # Check for transfer-related content
        return any(kw in text for kw in all_keywords)
    
    def _extract_image(self, entry) -> str:
        """Extract image URL from RSS entry"""
        # Try media_content first
        media = entry.get('media_content', [])
        if media and media[0].get('url'):
            return media[0]['url']
        
        # Try enclosures
        enclosures = entry.get('enclosures', [])
        if enclosures and enclosures[0].get('href'):
            return enclosures[0]['href']
        
        # Try links with image type
        for link in entry.get('links', []):
            if link.get('type', '').startswith('image'):
                return link.get('href', '')
        
        # Try media_thumbnail
        thumbs = entry.get('media_thumbnail', [])
        if thumbs and thumbs[0].get('url'):
            return thumbs[0]['url']
        
        return ""

    async def fetch_feed(self, feed_key: str) -> List[dict]:
        info = self.FEEDS.get(feed_key)
        if not info or feed_key in self.DISABLED_FEEDS:
            return []
        errors = getattr(self, "feed_errors", {})
        self.feed_errors = errors
        try:
            timeout = aiohttp.ClientTimeout(total=20, connect=5)
            headers = {"User-Agent": "TransferNewsDe/1.0 (+https://transfernews.de)"}
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(info["url"], max_redirects=5) as response:
                    if response.status != 200:
                        errors[feed_key] = f"http_{response.status}"
                        return []
                    chunks, size = [], 0
                    async for chunk in response.content.iter_chunked(65536):
                        size += len(chunk)
                        if size > 2 * 1024 * 1024:
                            errors[feed_key] = "feed_too_large"
                            return []
                        chunks.append(chunk)
                    content = b"".join(chunks)
            feed = await asyncio.to_thread(feedparser.parse, content)
            if not feed.entries and feed.get("bozo"):
                errors[feed_key] = "invalid_feed"
                return []
            events = []
            for entry in feed.entries[:50]:
                link = entry.get("link", "")
                if not self._entry_in_scope(info, link):
                    continue
                title = BeautifulSoup(entry.get("title", ""), "html.parser").get_text(" ", strip=True)
                summary = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(" ", strip=True)[:4000]
                if not self._is_transfer_related(title, summary, info.get("language", "de")):
                    continue
                source_time = parse_source_time(entry.get("published") or entry.get("updated"))
                events.append({
                    "headline_raw": title, "summary": summary, "source_url": link,
                    "source_key": feed_key, "source_name": info["name"],
                    "dedupe_key": self._generate_dedupe_key(title, feed_key, link, summary),
                    "legacy_dedupe_key": hashlib.md5(f"{title.lower()[:100]}:{feed_key}".encode()).hexdigest(),
                    "source_published_at": source_time, "image_url": self._extract_image(entry),
                    "language": info.get("language", "de"), "trust_score": info.get("trust_score", 70),
                    "category": info.get("category", "tier_3"),
                })
            return events
        except Exception as exc:
            errors[feed_key] = type(exc).__name__
            logger.warning("[RSS] %s fetch failed: %s", feed_key, type(exc).__name__)
            return []
    
    async def fetch_all_feeds(self) -> List[dict]:
        self.feed_errors = {}
        semaphore = asyncio.Semaphore(4)
        async def fetch(key):
            async with semaphore:
                return await self.fetch_feed(key)
        feeds = sorted(self.active_feeds(), key=lambda key: (self.FEEDS[key].get("category", "tier_3"), -self.FEEDS[key].get("trust_score", 0)))
        batches = await asyncio.gather(*(fetch(key) for key in feeds))
        return [event for batch in batches for event in batch]


async def import_rss_events(db) -> dict:
    """
    Import events from RSS feeds (international + German sources)
    """
    from models import Event, Source, EventType, EventStatus, SourceType, SourceCategory, generate_uuid
    
    result = {
        "new_events": 0, 
        "duplicates": 0, 
        "sources_created": 0,
        "by_language": {"de": 0, "en": 0, "es": 0},
        "by_tier": {"tier_1": 0, "tier_2": 0, "tier_3": 0}
    }
    
    scraper = RSSFeedScraper()
    
    # Ensure sources exist
    for source_key, source_info in scraper.active_feeds().items():
        existing = await db.sources.find_one({"slug": source_key})
        if not existing:
            source = Source(
                id=generate_uuid(),
                name=source_info["name"],
                slug=source_key,
                type=SourceType.MEDIA,
                source_url=source_info["url"],
                source_category=SourceCategory(source_info["category"]),
                active=True,
                trust_score=source_info.get("trust_score", 70),
            )
            await db.sources.insert_one(source.model_dump())
            result["sources_created"] += 1
    
    # Fetch all feeds
    events = await scraper.fetch_all_feeds()
    
    result["feed_errors"] = getattr(scraper, "feed_errors", {})
    result["feeds_checked"] = len(scraper.active_feeds())
    result["disabled_feeds"] = {key: dict(info) for key, info in scraper.DISABLED_FEEDS.items() if key in scraper.FEEDS}
    logger.info("[RSS] events=%s feeds=%s failed=%s disabled=%s", len(events), result["feeds_checked"], len(result["feed_errors"]), len(result["disabled_feeds"]))
    
    # Import events
    for event_data in events:
        # Check for duplicate
        existing = await db.events.find_one({"$or": [
            {"dedupe_key": event_data["dedupe_key"]},
            {"dedupe_key": event_data.get("legacy_dedupe_key", event_data["dedupe_key"]), "headline_raw": event_data["headline_raw"]}
        ]})
        if existing:
            result["duplicates"] += 1
            continue
        
        # Get source ID
        source = await db.sources.find_one({"slug": event_data["source_key"]})
        source_id = source["id"] if source else None
        
        # Determine event type (multilingual keywords)
        headline_lower = event_data["headline_raw"].lower()
        
        # Official/Confirmed keywords
        official_keywords = ["offiziell", "bestätigt", "fix", "unterschrieben", 
                           "official", "confirmed", "done deal", "here we go",
                           "oficial", "confirmado"]
        agreement_keywords = ["einigung", "agreement", "deal", "agrees terms",
                            "acuerdo", "personal terms", "medical"]
        
        if any(kw in headline_lower for kw in official_keywords):
            event_type = EventType.OFFICIAL
            confidence = 90
        elif any(kw in headline_lower for kw in agreement_keywords):
            event_type = EventType.CONFIRMED
            confidence = 75
        else:
            event_type = EventType.RUMOUR
            confidence = 50
        
        # Adjust confidence by trust score
        trust_score = event_data.get("trust_score", 70)
        confidence = min(95, confidence + (trust_score - 70) // 5)
        
        event = Event(
            id=generate_uuid(),
            event_type=event_type,
            status=EventStatus.PENDING,
            headline_raw=event_data["headline_raw"],
            body_raw=event_data.get("summary", ""),
            source_published_at=event_data.get("source_published_at"),
            source_id=source_id,
            source_url=event_data.get("source_url", ""),
            dedupe_key=event_data["dedupe_key"],
            confidence_score=confidence,
            image_url=event_data.get("image_url", ""),
        )
        
        # Add language metadata
        event_dict = event.model_dump()
        event_dict["_id"] = "rss:" + event_data["dedupe_key"]
        event_dict["title"] = event_data["headline_raw"]
        event_dict["summary"] = event_data.get("summary", "")
        event_dict["source_language"] = event_data.get("language", "de")
        event_dict["source_name"] = event_data.get("source_name", "")
        event_dict["source_category"] = event_data.get("category", "tier_3")
        
        try:
            await db.events.insert_one(event_dict)
        except DuplicateKeyError:
            result["duplicates"] += 1
            continue
        result["new_events"] += 1
        
        # Track stats
        lang = event_data.get("language", "de")
        tier = event_data.get("category", "tier_3")
        result["by_language"][lang] = result["by_language"].get(lang, 0) + 1
        result["by_tier"][tier] = result["by_tier"].get(tier, 0) + 1
    
    logger.info(f"[RSS] Import complete: {result}")
    return result


# ============================================================================
# IMAGE DOWNLOADER - Save images locally
# ============================================================================

import aiohttp
import os
from pathlib import Path

IMAGES_DIR = Path(os.environ.get("MEDIA_ROOT", str(Path(__file__).resolve().parent / "static"))) / "images"

async def download_and_save_image(image_url: str, article_id: str) -> str:
    """
    Download image from original source URL and save locally
    Returns the local path for the image
    """
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    if not image_url:
        return ""
    
    # Skip video URLs
    if ".m3u8" in image_url or "stream" in image_url:
        return ""
    
    try:
        # Determine file extension from content-type or URL
        ext = "jpg"
        if ".png" in image_url.lower():
            ext = "png"
        elif ".webp" in image_url.lower():
            ext = "webp"
        elif ".gif" in image_url.lower():
            ext = "gif"
        
        filename = f"{article_id}.{ext}"
        filepath = IMAGES_DIR / filename
        
        # Download with proper headers to avoid blocking
        async with aiohttp.ClientSession() as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            }
            
            # Add referer based on source
            if "t-online" in image_url:
                headers["Referer"] = "https://www.t-online.de/"
            elif "welt" in image_url:
                headers["Referer"] = "https://www.welt.de/"
            
            async with session.get(image_url, headers=headers, timeout=30, allow_redirects=True) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Check content type and adjust extension
                    content_type = response.headers.get("Content-Type", "")
                    if "webp" in content_type:
                        ext = "webp"
                        filename = f"{article_id}.{ext}"
                        filepath = IMAGES_DIR / filename
                    
                    # Only save if we got actual image data (> 1KB)
                    if len(content) > 1024:
                        with open(filepath, "wb") as f:
                            f.write(content)
                        logger.info(f"Downloaded image: {filename} ({len(content)} bytes)")
                        return f"/api/static/images/{filename}"
                    else:
                        logger.warning(f"Image too small: {len(content)} bytes")
                        return ""
                else:
                    logger.warning(f"Failed to download image: {response.status} - {image_url[:50]}")
                    return ""
    
    except Exception as e:
        logger.error(f"Image download error for {image_url[:50]}: {e}")
        return ""


async def download_fallback_image(article_id: str, keywords: str = "football") -> str:
    """
    Download a fallback image from Unsplash based on keywords
    """
    import random
    
    # Use Unsplash Source (no API key needed)
    rand = random.randint(1, 10000)
    url = f"https://source.unsplash.com/800x600/?{keywords}&sig={rand}"
    
    return await download_and_save_image(url, article_id)
