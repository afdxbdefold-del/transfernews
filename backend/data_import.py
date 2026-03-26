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
        existing = await db.events.find_one({"dedupe_key": event_data["dedupe_key"]})
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
from emergentintegrations.llm.chat import LlmChat, UserMessage


async def find_article_image(title: str) -> str:
    """
    Find a relevant image for the article based on keywords in title
    Uses Unsplash Source for free images
    """
    import re
    import random
    
    # Extract keywords from title
    title_lower = title.lower()
    
    # Map keywords to search terms
    keyword_map = {
        "bayern": "bayern munich football",
        "dortmund": "borussia dortmund football",
        "bundesliga": "bundesliga football stadium",
        "champions league": "champions league football",
        "nationalmannschaft": "germany national team football",
        "dfb": "germany football team",
        "transfer": "football player transfer",
        "trainer": "football coach",
        "tor": "football goal",
        "spieler": "football player",
        "fußball": "football soccer",
        "liverpool": "liverpool football",
        "real madrid": "real madrid football",
        "barcelona": "barcelona football",
        "premier league": "premier league football",
    }
    
    # Find matching keyword
    search_term = "football soccer match"  # default
    for keyword, term in keyword_map.items():
        if keyword in title_lower:
            search_term = term
            break
    
    # Use Unsplash Source (free, no API key needed)
    # Add random number to avoid caching same image
    rand = random.randint(1, 1000)
    return f"https://source.unsplash.com/800x600/?{search_term.replace(' ', ',')}&sig={rand}"


async def generate_article_from_event(event: dict, db) -> dict:
    """
    Generate a full article from a scraped event using LLM
    Returns the generated article data
    """
    from models import Article, ArticleType, ArticleStatus, generate_uuid
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise ValueError("EMERGENT_LLM_KEY nicht konfiguriert")
    
    headline = event.get("headline_raw", "")
    source_url = event.get("source_url", "")
    
    # Create LLM chat instance
    chat = LlmChat(
        api_key=api_key,
        session_id=f"article-gen-{event.get('id', 'new')}",
        system_message="""Du bist ein erfahrener Sportjournalist für eine deutsche Fußball-Transfer-News-Website.
Schreibe professionelle, sachliche und informative Artikel auf Deutsch.
Verwende einen journalistischen Stil ähnlich wie Kicker oder Sport1.
Erfinde keine Fakten - basiere alles auf der gegebenen Headline."""
    ).with_model("openai", "gpt-4o")
    
    # Generate title, excerpt and body
    prompt = f"""Basierend auf dieser Transfer-Meldung, erstelle einen Artikel:

HEADLINE: {headline}
QUELLE: {source_url}

Erstelle:
1. TITEL: Ein packender, SEO-optimierter Titel (max 80 Zeichen)
2. TEASER: Ein kurzer Teaser/Vorspann (max 200 Zeichen)
3. ARTIKEL: Der vollständige Artikel (3-4 Absätze, ca. 200-300 Wörter)

Formatiere die Antwort EXAKT so:
TITEL: [dein Titel]
TEASER: [dein Teaser]
ARTIKEL:
[dein Artikel]"""

    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    # Parse response
    title = headline  # Fallback
    excerpt = ""
    body = response
    
    lines = response.split("\n")
    current_section = None
    body_lines = []
    
    for line in lines:
        if line.startswith("TITEL:"):
            title = line.replace("TITEL:", "").strip()
        elif line.startswith("TEASER:"):
            excerpt = line.replace("TEASER:", "").strip()
        elif line.startswith("ARTIKEL:"):
            current_section = "body"
        elif current_section == "body":
            body_lines.append(line)
    
    if body_lines:
        body = "\n".join(body_lines).strip()
    
    # Generate slug
    slug = generate_slug(title)
    
    # Check if slug exists, append number if needed
    existing = await db.articles.find_one({"slug": slug})
    if existing:
        import random
        slug = f"{slug}-{random.randint(1000, 9999)}"
    
    # Get image from event or search for one
    source_image_url = event.get("image_url", "")
    article_id = generate_uuid()
    
    # Download original image from source
    image_url = ""
    if source_image_url:
        image_url = await download_and_save_image(source_image_url, article_id)
        if image_url:
            logger.info(f"Using original image for article: {title[:30]}")
    
    # Only use fallback if original download completely failed
    if not image_url:
        logger.warning(f"No original image, using fallback for: {title[:30]}")
        image_url = await download_fallback_image(article_id, "football,soccer")
    
    # Create article
    article = Article(
        id=article_id,
        title=title,
        slug=slug,
        excerpt=excerpt,
        body=body,
        article_type=ArticleType.NEWS,
        status=ArticleStatus.PUBLISHED,
        category="TRANSFER",
        source_event_id=event.get("id"),
        published_at=datetime.now(timezone.utc),
        feature_image=image_url,
    )
    
    return article.model_dump()


async def process_pending_events(db, limit: int = 5) -> dict:
    """
    Process pending events and generate articles
    Returns summary of processed events
    """
    from models import EventStatus, ArticleStatus
    
    result = {"processed": 0, "articles_created": 0, "errors": []}
    
    # Get pending events
    cursor = db.events.find({"status": "pending"}).limit(limit)
    events = await cursor.to_list(length=limit)
    
    for event in events:
        try:
            # Generate article
            article_data = await generate_article_from_event(event, db)
            
            # Save article
            await db.articles.insert_one(article_data)
            result["articles_created"] += 1
            
            # Update event status
            await db.events.update_one(
                {"id": event["id"]},
                {"$set": {"status": "processed", "generated_article_id": article_data["id"]}}
            )
            result["processed"] += 1
            
        except Exception as e:
            logger.error(f"Error processing event {event.get('id')}: {e}")
            result["errors"].append(str(e))
            
            # Mark as error
            await db.events.update_one(
                {"id": event["id"]},
                {"$set": {"status": "error", "error_message": str(e)}}
            )
    
    return result


# ============================================================================
# RSS FEED SCRAPER (More reliable than HTML scraping)
# ============================================================================

import feedparser

class RSSFeedScraper:
    """
    RSS Feed Scraper für Transfer-News
    """
    
    FEEDS = {
        "t_online_sport": {
            "url": "https://www.t-online.de/sport/feed.rss",
            "name": "T-Online Sport",
            "category": "tier_1",
        },
        "welt_sport": {
            "url": "https://www.welt.de/feeds/section/sport.rss",
            "name": "Welt Sport", 
            "category": "tier_2",
        },
        "focus_fussball": {
            "url": "https://rss.focus.de/fussball/",
            "name": "Focus Fußball",
            "category": "tier_2",
        },
    }
    
    TRANSFER_KEYWORDS = [
        "transfer", "wechsel", "verpflicht", "unterschr", "ablöse",
        "gerücht", "interesse", "verhandl", "angebot", "vertrag",
        "leihe", "ausstieg", "klausel", "millionen", "deal",
        "bundesliga", "dfb", "nationalmannschaft", "bayern", "dortmund",
        "fußball", "trainer", "spieler", "tor", "sieg", "niederlage"
    ]
    
    def _generate_dedupe_key(self, title: str, source: str) -> str:
        """Generate unique key for deduplication"""
        content = f"{title.lower()[:100]}:{source}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_transfer_related(self, title: str, summary: str = "") -> bool:
        """Check if article is transfer-related"""
        text = f"{title} {summary}".lower()
        return any(kw in text for kw in self.TRANSFER_KEYWORDS)
    
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
        """Fetch and parse a single RSS feed"""
        events = []
        feed_info = self.FEEDS.get(feed_key)
        if not feed_info:
            return events
        
        try:
            feed = feedparser.parse(feed_info["url"])
            
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")
                image_url = self._extract_image(entry)
                
                # Filter for transfer-related news
                if self._is_transfer_related(title, summary):
                    events.append({
                        "headline_raw": title,
                        "summary": summary[:500] if summary else "",
                        "source_url": link,
                        "source_key": feed_key,
                        "dedupe_key": self._generate_dedupe_key(title, feed_key),
                        "published": entry.get("published", ""),
                        "image_url": image_url,
                    })
        except Exception as e:
            logger.error(f"RSS feed error for {feed_key}: {e}")
        
        return events
    
    async def fetch_all_feeds(self) -> List[dict]:
        """Fetch all RSS feeds"""
        all_events = []
        
        for feed_key in self.FEEDS.keys():
            events = await self.fetch_feed(feed_key)
            all_events.extend(events)
        
        return all_events


async def import_rss_events(db) -> dict:
    """
    Import events from RSS feeds
    """
    from models import Event, Source, EventType, EventStatus, SourceType, SourceCategory, generate_uuid
    
    result = {"new_events": 0, "duplicates": 0, "sources_created": 0}
    
    scraper = RSSFeedScraper()
    
    # Ensure sources exist
    for source_key, source_info in scraper.FEEDS.items():
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
                trust_score=80 if source_info["category"] == "tier_1" else 60,
            )
            await db.sources.insert_one(source.model_dump())
            result["sources_created"] += 1
    
    # Fetch all feeds
    events = await scraper.fetch_all_feeds()
    
    # Import events
    for event_data in events:
        # Check for duplicate
        existing = await db.events.find_one({"dedupe_key": event_data["dedupe_key"]})
        if existing:
            result["duplicates"] += 1
            continue
        
        # Get source ID
        source = await db.sources.find_one({"slug": event_data["source_key"]})
        source_id = source["id"] if source else None
        
        # Determine event type
        headline_lower = event_data["headline_raw"].lower()
        if any(kw in headline_lower for kw in ["offiziell", "bestätigt", "fix", "unterschrieben"]):
            event_type = EventType.OFFICIAL
        elif any(kw in headline_lower for kw in ["einigung", "agreement", "deal"]):
            event_type = EventType.CONFIRMED
        else:
            event_type = EventType.RUMOUR
        
        event = Event(
            id=generate_uuid(),
            event_type=event_type,
            status=EventStatus.PENDING,
            headline_raw=event_data["headline_raw"],
            source_id=source_id,
            source_url=event_data.get("source_url", ""),
            dedupe_key=event_data["dedupe_key"],
            confidence_score=70 if event_type == EventType.OFFICIAL else 50,
            image_url=event_data.get("image_url", ""),
        )
        
        await db.events.insert_one(event.model_dump())
        result["new_events"] += 1
    
    return result


# ============================================================================
# IMAGE DOWNLOADER - Save images locally
# ============================================================================

import aiohttp
import os
from pathlib import Path

IMAGES_DIR = Path("/app/backend/static/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

async def download_and_save_image(image_url: str, article_id: str) -> str:
    """
    Download image from original source URL and save locally
    Returns the local path for the image
    """
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
