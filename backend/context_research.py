"""
TransferNews.de - KONTEXT-RECHERCHE SYSTEM
==========================================

Recherchiert echte Daten zu Spielern und Vereinen für längere,
faktenbasierte Artikel.

Quellen:
- Wikipedia (Spieler-Bio, Karriere)
- Vereins-Infos
- Transfermarkt-Daten (wenn verfügbar)
"""

import aiohttp
import asyncio
import logging
import re
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Wikipedia API für Spieler-/Vereins-Infos
WIKIPEDIA_API = "https://de.wikipedia.org/api/rest_v1/page/summary/"


class ContextResearcher:
    """
    Recherchiert Kontext-Informationen für Transfer-Artikel.
    Nutzt öffentliche APIs für echte Daten.
    """
    
    def __init__(self):
        self.cache = {}
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.headers = {
            "User-Agent": "TransferNewsDe/1.0 (https://transfernews.de; contact@transfernews.de) Python/aiohttp",
            "Accept": "application/json",
        }
    
    async def get_player_context(self, player_name: str) -> Dict:
        """
        Holt Spieler-Informationen aus Wikipedia.
        
        Returns:
            {
                "found": True/False,
                "summary": "Kurze Bio",
                "birth_year": 1999,
                "nationality": "Deutschland",
                "position": "Mittelfeld",
                "current_club": "...",
                "career_highlights": ["...", "..."],
            }
        """
        if not player_name or player_name == "Unbekannter Spieler":
            return {"found": False}
        
        # Cache prüfen
        cache_key = f"player:{player_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Wikipedia-Suche
            wiki_name = player_name.replace(" ", "_")
            
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                # Versuche deutsche Wikipedia
                url = f"{WIKIPEDIA_API}{wiki_name}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        extract = data.get("extract", "")
                        
                        # Parse relevante Infos
                        result = {
                            "found": True,
                            "summary": extract[:500] if extract else "",
                            "source": "Wikipedia",
                        }
                        
                        # Versuche Geburtsjahr zu extrahieren (vierstellige Zahl zwischen 1970-2010)
                        year_match = re.search(r'\b(19[789]\d|200\d|201[0-5])\b', extract)
                        if year_match:
                            year = int(year_match.group(1))
                            # Validiere: Spieler sollten 15-50 Jahre alt sein
                            current_year = datetime.now().year
                            age = current_year - year
                            if 15 <= age <= 50:
                                result["birth_year"] = year
                        
                        # Position erkennen
                        positions = {
                            "stürmer": "Stürmer",
                            "mittelfeld": "Mittelfeldspieler", 
                            "verteidiger": "Verteidiger",
                            "torwart": "Torwart",
                            "torhüter": "Torwart",
                            "flügel": "Flügelspieler",
                            "außen": "Außenspieler",
                        }
                        extract_lower = extract.lower()
                        for key, pos in positions.items():
                            if key in extract_lower:
                                result["position"] = pos
                                break
                        
                        # Nationalität erkennen
                        nationalities = [
                            "deutsch", "englisch", "französisch", "spanisch",
                            "italienisch", "portugiesisch", "niederländisch",
                            "belgisch", "brasilianisch", "argentinisch",
                        ]
                        for nat in nationalities:
                            if nat in extract_lower:
                                result["nationality"] = nat.capitalize() + "er"
                                break
                        
                        self.cache[cache_key] = result
                        logger.info(f"[CONTEXT] Found Wikipedia data for {player_name}")
                        return result
                    
        except Exception as e:
            logger.debug(f"[CONTEXT] Wikipedia lookup failed for {player_name}: {e}")
        
        return {"found": False}
    
    async def get_club_context(self, club_name: str) -> Dict:
        """
        Holt Vereins-Informationen.
        
        Returns:
            {
                "found": True/False,
                "summary": "Kurze Beschreibung",
                "league": "Bundesliga",
                "country": "Deutschland",
                "stadium": "...",
                "founded": 1900,
            }
        """
        if not club_name or club_name == "Unbekannter Verein":
            return {"found": False}
        
        cache_key = f"club:{club_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            wiki_name = club_name.replace(" ", "_")
            
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                url = f"{WIKIPEDIA_API}{wiki_name}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        extract = data.get("extract", "")
                        
                        result = {
                            "found": True,
                            "summary": extract[:400] if extract else "",
                            "source": "Wikipedia",
                        }
                        
                        # Liga erkennen
                        leagues = {
                            "bundesliga": "Bundesliga",
                            "premier league": "Premier League",
                            "la liga": "La Liga",
                            "serie a": "Serie A",
                            "ligue 1": "Ligue 1",
                        }
                        extract_lower = extract.lower()
                        for key, league in leagues.items():
                            if key in extract_lower:
                                result["league"] = league
                                break
                        
                        self.cache[cache_key] = result
                        logger.info(f"[CONTEXT] Found Wikipedia data for {club_name}")
                        return result
                        
        except Exception as e:
            logger.debug(f"[CONTEXT] Wikipedia lookup failed for {club_name}: {e}")
        
        return {"found": False}
    
    async def research_transfer(
        self,
        player_name: str,
        from_club: Optional[str] = None,
        to_club: Optional[str] = None,
    ) -> Dict:
        """
        Führt vollständige Recherche für einen Transfer durch.
        
        Returns:
            {
                "player": {...},
                "from_club": {...},
                "to_club": {...},
                "context_text": "Zusammengefasster Kontext für GPT",
            }
        """
        # Parallele Recherche
        tasks = [self.get_player_context(player_name)]
        if from_club:
            tasks.append(self.get_club_context(from_club))
        if to_club:
            tasks.append(self.get_club_context(to_club))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        player_data = results[0] if not isinstance(results[0], Exception) else {"found": False}
        from_club_data = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else {"found": False}
        to_club_data = results[2] if len(results) > 2 and not isinstance(results[2], Exception) else {"found": False}
        
        # Kontext-Text für GPT generieren
        context_parts = []
        
        if player_data.get("found"):
            player_info = []
            if player_data.get("summary"):
                # Kürze auf relevanten Teil
                summary = player_data["summary"]
                # Erste 2 Sätze
                sentences = summary.split(". ")[:2]
                player_info.append(". ".join(sentences) + ".")
            if player_data.get("position"):
                player_info.append(f"Position: {player_data['position']}")
            if player_data.get("birth_year"):
                age = datetime.now().year - player_data["birth_year"]
                player_info.append(f"Alter: {age} Jahre")
            if player_data.get("nationality"):
                player_info.append(f"Nationalität: {player_data['nationality']}")
            
            if player_info:
                context_parts.append(f"SPIELER-INFO ({player_name}):\n" + "\n".join(player_info))
        
        if to_club_data.get("found") and to_club_data.get("summary"):
            summary = to_club_data["summary"]
            sentences = summary.split(". ")[:2]
            context_parts.append(f"ZIELVEREIN ({to_club}):\n" + ". ".join(sentences) + ".")
        
        if from_club_data.get("found") and from_club_data.get("summary"):
            summary = from_club_data["summary"]
            sentences = summary.split(". ")[:1]
            context_parts.append(f"AKTUELLER VEREIN ({from_club}):\n" + ". ".join(sentences) + ".")
        
        return {
            "player": player_data,
            "from_club": from_club_data,
            "to_club": to_club_data,
            "context_text": "\n\n".join(context_parts) if context_parts else "",
            "has_context": len(context_parts) > 0,
        }


# Singleton
_researcher = None

def get_context_researcher() -> ContextResearcher:
    global _researcher
    if _researcher is None:
        _researcher = ContextResearcher()
    return _researcher
