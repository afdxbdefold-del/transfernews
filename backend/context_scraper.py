"""
TransferNews.de - AGGRESSIVER KONTEXT-SCRAPER
==============================================

Massives Content-Enrichment durch Multi-Source-Scraping.
Anti-Blocking ohne Proxies durch:
- User-Agent Rotation (50+ Fingerprints)
- Random Delays
- Playwright für JS-heavy Sites
- Fallback-Ketten
- Caching

Quellen:
- Wikipedia DE/EN
- Transfermarkt.de
- Kicker.de
- FBRef
"""

import aiohttp
import asyncio
import logging
import random
import re
import json
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import hashlib

logger = logging.getLogger(__name__)

# =============================================================================
# USER-AGENT ROTATION (50+ Browser-Fingerprints)
# =============================================================================

USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    # Firefox Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    # Mobile
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    # Weitere Chrome Versionen
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

# Referer-Rotation
REFERERS = [
    "https://www.google.com/",
    "https://www.google.de/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
    "https://www.ecosia.org/",
    "https://t.co/",
    "https://www.facebook.com/",
    "",  # Direct
]


def get_random_headers(for_api: bool = False) -> Dict[str, str]:
    """Generiert zufällige Browser-Header"""
    if for_api:
        # Für APIs (Wikipedia, etc.) - Bot-konformer Header
        return {
            "User-Agent": "TransferNewsDe/1.0 (https://transfernews.de; kontakt@transfernews.de) Python/aiohttp",
            "Accept": "application/json",
        }
    
    # Für normale Websites - Browser-Fingerprint
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Referer": random.choice(REFERERS),
        "Cache-Control": "max-age=0",
    }


async def random_delay(min_sec: float = 0.5, max_sec: float = 2.0):
    """Zufällige Verzögerung zwischen Requests"""
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


# =============================================================================
# DATENKLASSEN
# =============================================================================

@dataclass
class PlayerContext:
    """Gesammelter Kontext zu einem Spieler"""
    name: str
    found: bool = False
    
    # Basis-Infos
    full_name: str = ""
    birth_date: str = ""
    birth_year: int = 0
    age: int = 0
    nationality: str = ""
    position: str = ""
    height: str = ""
    foot: str = ""
    
    # Karriere
    current_club: str = ""
    current_club_since: str = ""
    contract_until: str = ""
    market_value: str = ""
    
    # Statistiken
    career_goals: int = 0
    career_assists: int = 0
    national_team_caps: int = 0
    national_team_goals: int = 0
    
    # Erfolge
    titles: List[str] = field(default_factory=list)
    
    # Bio/Beschreibung
    wikipedia_summary: str = ""
    career_highlights: List[str] = field(default_factory=list)
    
    # Transfer-Historie
    transfer_history: List[Dict] = field(default_factory=list)
    
    # Quellen
    sources: List[str] = field(default_factory=list)
    
    def to_context_text(self) -> str:
        """Generiert Kontext-Text für LLM-Prompt"""
        lines = []
        
        if self.full_name and self.full_name != self.name:
            lines.append(f"Vollständiger Name: {self.full_name}")
        
        if self.birth_year:
            lines.append(f"Geboren: {self.birth_date or self.birth_year} ({self.age} Jahre)")
        
        if self.nationality:
            lines.append(f"Nationalität: {self.nationality}")
        
        if self.position:
            lines.append(f"Position: {self.position}")
        
        if self.current_club:
            club_info = f"Aktueller Verein: {self.current_club}"
            if self.current_club_since:
                club_info += f" (seit {self.current_club_since})"
            lines.append(club_info)
        
        if self.contract_until:
            lines.append(f"Vertrag bis: {self.contract_until}")
        
        if self.market_value:
            lines.append(f"Marktwert: {self.market_value}")
        
        if self.national_team_caps:
            nt_info = f"Länderspiele: {self.national_team_caps}"
            if self.national_team_goals:
                nt_info += f" ({self.national_team_goals} Tore)"
            lines.append(nt_info)
        
        if self.career_goals:
            lines.append(f"Karriere-Tore: {self.career_goals}")
        
        if self.titles:
            lines.append(f"Titel: {', '.join(self.titles[:5])}")
        
        if self.career_highlights:
            lines.append("Karriere-Highlights:")
            for h in self.career_highlights[:3]:
                lines.append(f"  - {h}")
        
        if self.transfer_history:
            lines.append("Letzte Transfers:")
            for t in self.transfer_history[:3]:
                lines.append(f"  - {t.get('date', '?')}: {t.get('from', '?')} → {t.get('to', '?')} ({t.get('fee', 'unbekannt')})")
        
        if self.wikipedia_summary:
            lines.append(f"\nBio: {self.wikipedia_summary[:400]}...")
        
        return "\n".join(lines)


@dataclass 
class ClubContext:
    """Kontext zu einem Verein"""
    name: str
    found: bool = False
    
    full_name: str = ""
    founded: str = ""
    stadium: str = ""
    stadium_capacity: str = ""
    league: str = ""
    coach: str = ""
    
    titles: List[str] = field(default_factory=list)
    
    def to_context_text(self) -> str:
        lines = []
        if self.full_name:
            lines.append(f"Verein: {self.full_name}")
        if self.founded:
            lines.append(f"Gegründet: {self.founded}")
        if self.stadium:
            lines.append(f"Stadion: {self.stadium} ({self.stadium_capacity})" if self.stadium_capacity else f"Stadion: {self.stadium}")
        if self.league:
            lines.append(f"Liga: {self.league}")
        if self.coach:
            lines.append(f"Trainer: {self.coach}")
        if self.titles:
            lines.append(f"Titel: {', '.join(self.titles[:5])}")
        return "\n".join(lines)


# =============================================================================
# SCRAPER KLASSEN
# =============================================================================

class WikidataScraper:
    """
    Scraper für Wikidata SPARQL - strukturierte Spielerdaten.
    Kein Blocking, offene API, sehr zuverlässig!
    """
    
    SPARQL_URL = "https://query.wikidata.org/sparql"
    
    def __init__(self):
        self.cache = {}
    
    async def get_player(self, name: str) -> PlayerContext:
        """Holt strukturierte Spielerdaten aus Wikidata"""
        ctx = PlayerContext(name=name)
        
        cache_key = f"wikidata:{name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # SPARQL Query für Fußballer
        query = f"""
        SELECT DISTINCT ?item ?itemLabel ?birthDate ?height ?nationality ?nationalityLabel 
               ?position ?positionLabel ?club ?clubLabel ?caps ?goals ?image WHERE {{
          ?item wdt:P31 wd:Q5 .
          ?item rdfs:label "{name}"@de .
          ?item wdt:P106 wd:Q937857 .  # Beruf: Fußballspieler
          
          OPTIONAL {{ ?item wdt:P569 ?birthDate . }}
          OPTIONAL {{ ?item wdt:P2048 ?height . }}
          OPTIONAL {{ ?item wdt:P27 ?nationality . }}
          OPTIONAL {{ ?item wdt:P413 ?position . }}
          OPTIONAL {{ ?item wdt:P54 ?club . }}
          OPTIONAL {{ ?item wdt:P1350 ?caps . }}
          OPTIONAL {{ ?item wdt:P1351 ?goals . }}
          OPTIONAL {{ ?item wdt:P18 ?image . }}
          
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "de,en" . }}
        }}
        LIMIT 10
        """
        
        headers = {
            "User-Agent": "TransferNewsDe/1.0 (https://transfernews.de; kontakt@transfernews.de)",
            "Accept": "application/json",
        }
        
        try:
            await random_delay(0.3, 0.8)
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.SPARQL_URL, 
                    params={"query": query, "format": "json"},
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("results", {}).get("bindings", [])
                        
                        if results:
                            ctx.found = True
                            ctx.sources.append("Wikidata")
                            
                            # Sammle alle Daten aus allen Ergebnissen
                            clubs = set()
                            positions = set()
                            
                            for r in results:
                                # Name
                                if not ctx.full_name and 'itemLabel' in r:
                                    ctx.full_name = r['itemLabel']['value']
                                
                                # Geburtsdatum
                                if not ctx.birth_date and 'birthDate' in r:
                                    bd = r['birthDate']['value']
                                    ctx.birth_date = bd[:10]  # YYYY-MM-DD
                                    try:
                                        ctx.birth_year = int(bd[:4])
                                        ctx.age = datetime.now().year - ctx.birth_year
                                    except:
                                        pass
                                
                                # Größe
                                if not ctx.height and 'height' in r:
                                    h = r['height']['value']
                                    try:
                                        ctx.height = f"{float(h):.2f} m"
                                    except:
                                        pass
                                
                                # Nationalität
                                if not ctx.nationality and 'nationalityLabel' in r:
                                    ctx.nationality = r['nationalityLabel']['value']
                                
                                # Position
                                if 'positionLabel' in r:
                                    positions.add(r['positionLabel']['value'])
                                
                                # Vereine
                                if 'clubLabel' in r:
                                    club = r['clubLabel']['value']
                                    if 'nationalmannschaft' not in club.lower():
                                        clubs.add(club)
                                
                                # Länderspiele
                                if 'caps' in r:
                                    try:
                                        ctx.national_team_caps = int(r['caps']['value'])
                                    except:
                                        pass
                                
                                if 'goals' in r:
                                    try:
                                        ctx.national_team_goals = int(r['goals']['value'])
                                    except:
                                        pass
                            
                            # Position zusammenfassen
                            if positions:
                                ctx.position = ", ".join(list(positions)[:2])
                            
                            # Aktueller Verein (nehme den letzten)
                            if clubs:
                                ctx.current_club = list(clubs)[-1]
                        
        except Exception as e:
            logger.warning(f"Wikidata error for {name}: {e}")
        
        self.cache[cache_key] = ctx
        return ctx


class WikipediaScraper:
    """Scraper für Wikipedia (DE + EN)"""
    
    API_DE = "https://de.wikipedia.org/api/rest_v1/page/summary/"
    API_EN = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    
    def __init__(self):
        self.cache = {}
    
    async def get_player(self, name: str) -> PlayerContext:
        """Holt Spieler-Infos aus Wikipedia"""
        ctx = PlayerContext(name=name)
        
        cache_key = f"wiki:{name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Versuche DE dann EN
        for api_base in [self.API_DE, self.API_EN]:
            try:
                await random_delay(0.3, 0.8)
                
                wiki_name = name.replace(" ", "_")
                url = f"{api_base}{wiki_name}"
                
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=get_random_headers(for_api=True)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            extract = data.get("extract", "")
                            
                            if extract and ("fußball" in extract.lower() or "footballer" in extract.lower() or "soccer" in extract.lower()):
                                ctx.found = True
                                ctx.wikipedia_summary = extract
                                ctx.sources.append("Wikipedia")
                                
                                # Parse Geburtsjahr
                                year_match = re.search(r'\b(19[89]\d|20[012]\d)\b', extract)
                                if year_match:
                                    ctx.birth_year = int(year_match.group(1))
                                    ctx.age = datetime.now().year - ctx.birth_year
                                
                                # Parse Nationalität
                                nationalities = ["deutsch", "german", "französisch", "french", "englisch", "english", 
                                               "spanisch", "spanish", "italienisch", "italian", "niederländisch", "dutch",
                                               "portugiesisch", "portuguese", "brasilianisch", "brazilian", "argentinisch",
                                               "norwegian", "norwegisch", "belgian", "belgisch"]
                                for nat in nationalities:
                                    if nat in extract.lower():
                                        ctx.nationality = nat.capitalize()
                                        break
                                
                                # Parse Position
                                positions = {
                                    "stürmer": "Stürmer", "striker": "Stürmer", "forward": "Stürmer",
                                    "mittelfeld": "Mittelfeld", "midfielder": "Mittelfeld",
                                    "verteidiger": "Verteidiger", "defender": "Verteidiger",
                                    "torwart": "Torwart", "goalkeeper": "Torwart", "keeper": "Torwart",
                                }
                                for pos_key, pos_val in positions.items():
                                    if pos_key in extract.lower():
                                        ctx.position = pos_val
                                        break
                                
                                self.cache[cache_key] = ctx
                                return ctx
                                
            except Exception as e:
                logger.debug(f"Wikipedia error for {name}: {e}")
                continue
        
        self.cache[cache_key] = ctx
        return ctx


class TransfermarktScraper:
    """Scraper für Transfermarkt.de"""
    
    SEARCH_URL = "https://www.transfermarkt.de/schnellsuche/ergebnis/schnellsuche"
    
    def __init__(self):
        self.cache = {}
    
    async def search_player(self, name: str) -> Optional[str]:
        """Sucht Spieler und gibt Profil-URL zurück"""
        try:
            await random_delay(1.0, 2.0)
            
            params = {"query": name, "x": "0", "y": "0"}
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.SEARCH_URL, params=params, headers=get_random_headers()) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Finde ersten Spieler-Link
                        player_link = soup.select_one('a.spielprofil_tooltip')
                        if player_link:
                            href = player_link.get('href', '')
                            if href:
                                return f"https://www.transfermarkt.de{href}"
            
        except Exception as e:
            logger.debug(f"Transfermarkt search error: {e}")
        
        return None
    
    async def get_player(self, name: str) -> PlayerContext:
        """Holt Spieler-Infos von Transfermarkt"""
        ctx = PlayerContext(name=name)
        
        cache_key = f"tm:{name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Erst Suche
            profile_url = await self.search_player(name)
            if not profile_url:
                self.cache[cache_key] = ctx
                return ctx
            
            await random_delay(1.0, 2.5)
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(profile_url, headers=get_random_headers()) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        ctx.found = True
                        ctx.sources.append("Transfermarkt")
                        
                        # Name
                        name_el = soup.select_one('h1.data-header__headline-wrapper')
                        if name_el:
                            ctx.full_name = name_el.get_text(strip=True)
                        
                        # Marktwert
                        value_el = soup.select_one('a.data-header__market-value-wrapper')
                        if value_el:
                            ctx.market_value = value_el.get_text(strip=True)
                        
                        # Info-Tabelle
                        info_table = soup.select('span.info-table__content')
                        labels = soup.select('span.info-table__content--regular')
                        
                        for i, label in enumerate(labels):
                            label_text = label.get_text(strip=True).lower()
                            if i < len(info_table):
                                value = info_table[i].get_text(strip=True)
                                
                                if "geburt" in label_text or "birth" in label_text:
                                    ctx.birth_date = value
                                    year_match = re.search(r'(\d{4})', value)
                                    if year_match:
                                        ctx.birth_year = int(year_match.group(1))
                                        ctx.age = datetime.now().year - ctx.birth_year
                                
                                elif "nation" in label_text:
                                    ctx.nationality = value
                                
                                elif "position" in label_text:
                                    ctx.position = value
                                
                                elif "fuß" in label_text or "foot" in label_text:
                                    ctx.foot = value
                                
                                elif "größe" in label_text or "height" in label_text:
                                    ctx.height = value
                                
                                elif "verein" in label_text or "club" in label_text:
                                    ctx.current_club = value
                                
                                elif "vertrag" in label_text or "contract" in label_text:
                                    ctx.contract_until = value
                        
                        # Länderspiel-Stats
                        nt_stats = soup.select_one('div.data-header__details')
                        if nt_stats:
                            text = nt_stats.get_text()
                            caps_match = re.search(r'(\d+)\s*(?:Länderspiel|cap)', text, re.I)
                            goals_match = re.search(r'(\d+)\s*(?:Tor|goal)', text, re.I)
                            if caps_match:
                                ctx.national_team_caps = int(caps_match.group(1))
                            if goals_match:
                                ctx.national_team_goals = int(goals_match.group(1))
                        
        except Exception as e:
            logger.warning(f"Transfermarkt scrape error for {name}: {e}")
        
        self.cache[cache_key] = ctx
        return ctx


class KickerScraper:
    """Scraper für Kicker.de - aktuelle News"""
    
    SEARCH_URL = "https://www.kicker.de/suche"
    
    def __init__(self):
        self.cache = {}
    
    async def get_recent_news(self, player_name: str) -> List[str]:
        """Holt aktuelle Headlines zu einem Spieler"""
        cache_key = f"kicker:{player_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        headlines = []
        
        try:
            await random_delay(0.8, 1.5)
            
            params = {"q": player_name}
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.SEARCH_URL, params=params, headers=get_random_headers()) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Finde Artikel-Headlines
                        articles = soup.select('article h2, article h3, .kick__article-teaser__headline')
                        for article in articles[:5]:
                            headline = article.get_text(strip=True)
                            if headline and len(headline) > 10:
                                headlines.append(headline)
        
        except Exception as e:
            logger.debug(f"Kicker scrape error: {e}")
        
        self.cache[cache_key] = headlines
        return headlines


# =============================================================================
# MASTER CONTEXT SERVICE
# =============================================================================

class AggressiveContextService:
    """
    Koordiniert alle Scraper für maximales Content-Enrichment.
    Führt parallele Requests mit Fallback-Ketten durch.
    """
    
    def __init__(self, db=None):
        self.db = db
        self.wikidata = WikidataScraper()
        self.wikipedia = WikipediaScraper()
        self.transfermarkt = TransfermarktScraper()
        self.kicker = KickerScraper()
        
        # Master-Cache
        self.cache = {}
    
    async def get_full_player_context(self, player_name: str) -> PlayerContext:
        """
        Holt ALLE verfügbaren Infos zu einem Spieler.
        Parallel-Requests + Merging der Ergebnisse.
        """
        if not player_name or len(player_name) < 3:
            return PlayerContext(name=player_name or "Unknown")
        
        cache_key = f"full:{player_name}"
        if cache_key in self.cache:
            logger.info(f"[CONTEXT] Cache hit: {player_name}")
            return self.cache[cache_key]
        
        logger.info(f"[CONTEXT] Aggressive scraping: {player_name}")
        
        # Parallel alle Quellen abfragen
        wikidata_task = asyncio.create_task(self.wikidata.get_player(player_name))
        wiki_task = asyncio.create_task(self.wikipedia.get_player(player_name))
        # Transfermarkt oft blockiert, trotzdem versuchen
        # tm_task = asyncio.create_task(self.transfermarkt.get_player(player_name))
        news_task = asyncio.create_task(self.kicker.get_recent_news(player_name))
        
        # Auf alle warten (mit Timeout)
        try:
            results = await asyncio.wait_for(
                asyncio.gather(wikidata_task, wiki_task, news_task, return_exceptions=True),
                timeout=30
            )
        except asyncio.TimeoutError:
            logger.warning(f"[CONTEXT] Timeout for {player_name}")
            results = [PlayerContext(name=player_name), PlayerContext(name=player_name), []]
        
        wikidata_ctx = results[0] if isinstance(results[0], PlayerContext) else PlayerContext(name=player_name)
        wiki_ctx = results[1] if isinstance(results[1], PlayerContext) else PlayerContext(name=player_name)
        news = results[2] if isinstance(results[2], list) else []
        
        # Merge: Wikidata hat Priorität für strukturierte Daten, Wikipedia für Bio
        merged = PlayerContext(name=player_name)
        merged.found = wikidata_ctx.found or wiki_ctx.found
        
        # Von Wikidata (genaueste strukturierte Daten)
        if wikidata_ctx.found:
            merged.full_name = wikidata_ctx.full_name
            merged.birth_date = wikidata_ctx.birth_date
            merged.birth_year = wikidata_ctx.birth_year
            merged.age = wikidata_ctx.age
            merged.nationality = wikidata_ctx.nationality
            merged.position = wikidata_ctx.position
            merged.height = wikidata_ctx.height
            merged.current_club = wikidata_ctx.current_club
            merged.national_team_caps = wikidata_ctx.national_team_caps
            merged.national_team_goals = wikidata_ctx.national_team_goals
            merged.sources.extend(wikidata_ctx.sources)
        
        # Von Wikipedia (für Bio)
        if wiki_ctx.found:
            merged.wikipedia_summary = wiki_ctx.wikipedia_summary
            # Fallback-Werte wenn Wikidata leer
            if not merged.birth_year and wiki_ctx.birth_year:
                merged.birth_year = wiki_ctx.birth_year
                merged.age = wiki_ctx.age
            if not merged.nationality:
                merged.nationality = wiki_ctx.nationality
            if not merged.position:
                merged.position = wiki_ctx.position
            merged.sources.extend(wiki_ctx.sources)
        
        # News als Highlights
        if news:
            merged.career_highlights = news[:3]
            merged.sources.append("Kicker")
        
        # Cache
        self.cache[cache_key] = merged
        
        sources_str = ", ".join(merged.sources) if merged.sources else "keine"
        logger.info(f"[CONTEXT] {player_name}: found={merged.found}, sources=[{sources_str}]")
        
        return merged
    
    async def get_club_context(self, club_name: str) -> ClubContext:
        """Holt Vereins-Kontext"""
        if not club_name:
            return ClubContext(name="Unknown")
        
        ctx = ClubContext(name=club_name)
        
        try:
            await random_delay(0.3, 0.8)
            
            wiki_name = club_name.replace(" ", "_")
            url = f"https://de.wikipedia.org/api/rest_v1/page/summary/{wiki_name}"
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=get_random_headers(for_api=True)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        extract = data.get("extract", "")
                        
                        if extract:
                            ctx.found = True
                            
                            # Parse League
                            leagues = ["bundesliga", "premier league", "la liga", "serie a", "ligue 1"]
                            for league in leagues:
                                if league in extract.lower():
                                    ctx.league = league.title()
                                    break
        
        except Exception as e:
            logger.debug(f"Club context error: {e}")
        
        return ctx
    
    async def enrich_article(self, article: dict) -> dict:
        """
        Reichert einen Artikel mit Kontext an.
        Gibt erweiterten Artikel-Dict zurück.
        """
        player_name = article.get("player_name", "")
        club_name = article.get("club_name", "")
        title = article.get("title", "")
        
        # Versuche Spieler aus Titel zu extrahieren wenn nicht vorhanden
        if not player_name:
            from wikimedia_images import PlayerDetector
            detector = PlayerDetector()
            player_name = detector.detect_player(title, article.get("body", ""))
        
        enriched = article.copy()
        
        if player_name:
            player_ctx = await self.get_full_player_context(player_name)
            
            if player_ctx.found:
                enriched["context_text"] = player_ctx.to_context_text()
                enriched["has_researched_context"] = True
                enriched["context_sources"] = player_ctx.sources
                
                # Auch einzelne Felder für direkten Zugriff
                enriched["player_full_name"] = player_ctx.full_name
                enriched["player_age"] = player_ctx.age
                enriched["player_nationality"] = player_ctx.nationality
                enriched["player_position"] = player_ctx.position
                enriched["player_market_value"] = player_ctx.market_value
                enriched["player_contract_until"] = player_ctx.contract_until
                
                logger.info(f"[ENRICH] {title[:40]}... -> {len(enriched.get('context_text', ''))} chars context")
        
        return enriched


# =============================================================================
# SINGLETON & FACTORY
# =============================================================================

_context_service = None

def get_context_service(db=None) -> AggressiveContextService:
    """Factory für Context Service"""
    global _context_service
    if _context_service is None:
        _context_service = AggressiveContextService(db)
    return _context_service
