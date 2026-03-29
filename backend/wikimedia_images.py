"""
TransferNews.de - WIKIMEDIA BILDSYSTEM
=======================================

Robustes, einfaches Bildsystem für automatische Artikelbilder.
- Spieler-Erkennung aus Artikeltext
- Wikimedia Commons Suche
- Lizenzprüfung
- Quality-Scoring
- Fallback-System
- Attribution-Generierung
"""

import aiohttp
import asyncio
import hashlib
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

# =============================================================================
# KONFIGURATION
# =============================================================================

# Mindestanforderungen für Google Discover
MIN_WIDTH = 1200
MIN_HEIGHT = 675
PREFERRED_RATIO = 16 / 9

# Akzeptierte Lizenzen (kommerziell nutzbar)
ALLOWED_LICENSES = [
    # CC-BY-SA Varianten
    "cc-by-sa", "cc by-sa", "cc by sa",
    # CC-BY Varianten  
    "cc-by", "cc by",
    # CC0 / Public Domain
    "cc-zero", "cc0", "cc 0", "public domain", "pd", "pd-",
    # GFDL und FAL
    "gfdl", "fal",
    # Attribution
    "attribution",
]

# Begriffe die KEINE Spieler sind
IGNORED_TERMS = {
    # Ligen
    "bundesliga", "premier league", "la liga", "serie a", "ligue 1",
    "champions league", "europa league", "conference league",
    # Deutsche Clubs
    "bayern", "dortmund", "leipzig", "leverkusen", "frankfurt",
    "wolfsburg", "freiburg", "mainz", "köln", "stuttgart", "schalke",
    "gladbach", "bremen", "hertha", "hoffenheim", "augsburg", "bochum",
    "union berlin", "heidenheim",
    # Internationale Clubs
    "real madrid", "barcelona", "atletico madrid", "sevilla", "valencia",
    "manchester", "liverpool", "chelsea", "arsenal", "tottenham",
    "juventus", "milan", "inter", "napoli", "roma",
    "paris", "psg", "marseille", "lyon",
    # Allgemeine Begriffe
    "transfer", "transfers", "gerücht", "gerüchte", "wechsel",
    "trainer", "manager", "coach", "verein", "club", "team",
    "saison", "spieltag", "tabelle", "ergebnis", "spiel",
    "millionen", "euro", "ablöse", "vertrag", "zukunft",
    "offiziell", "bestätigt", "interesse", "verhandlung",
    # Wörter die oft am Ende stehen
    "madrid", "city", "united",
}

# Fallback-Bilder (eigene, lizenzfreie Bilder)
FALLBACK_IMAGES = {
    "stadium": {
        "url": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=1200",
        "attribution": "Unsplash",
        "license": "Unsplash License",
    },
    "football": {
        "url": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=1200",
        "attribution": "Unsplash", 
        "license": "Unsplash License",
    },
    "fans": {
        "url": "https://images.unsplash.com/photo-1459865264687-595d652de67e?w=1200",
        "attribution": "Unsplash",
        "license": "Unsplash License",
    },
    "match": {
        "url": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=1200",
        "attribution": "Unsplash",
        "license": "Unsplash License",
    },
}


class ImageStatus(str, Enum):
    """Status des Artikelbildes"""
    FOUND = "found"              # Wikimedia-Bild gefunden
    FALLBACK = "fallback"        # Fallback verwendet
    NO_PLAYER = "no_player"      # Kein Spieler erkannt
    NO_RESULTS = "no_results"    # Keine Treffer
    LOW_QUALITY = "low_quality"  # Treffer zu schlecht
    BAD_LICENSE = "bad_license"  # Lizenz ungeeignet
    MANUAL = "manual"            # Manuell gesetzt
    PENDING = "pending"          # Noch nicht verarbeitet


@dataclass
class WikimediaImage:
    """Wikimedia-Bild mit Metadaten"""
    url: str
    width: int
    height: int
    title: str
    license_name: str
    license_url: str
    author: str
    author_url: str
    source_url: str
    search_term: str
    quality_score: int = 0
    is_valid: bool = False
    rejection_reason: str = ""


@dataclass
class ArticleImage:
    """Gespeichertes Artikelbild"""
    url: str
    width: int
    height: int
    status: ImageStatus
    license_name: str = ""
    license_url: str = ""
    author: str = ""
    author_url: str = ""
    source_url: str = ""
    search_term: str = ""
    detected_player: str = ""
    quality_score: int = 0
    error_reason: str = ""
    is_fallback: bool = False
    fallback_category: str = ""
    created_at: str = ""
    
    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "width": self.width,
            "height": self.height,
            "status": self.status.value,
            "license_name": self.license_name,
            "license_url": self.license_url,
            "author": self.author,
            "author_url": self.author_url,
            "source_url": self.source_url,
            "search_term": self.search_term,
            "detected_player": self.detected_player,
            "quality_score": self.quality_score,
            "error_reason": self.error_reason,
            "is_fallback": self.is_fallback,
            "fallback_category": self.fallback_category,
            "created_at": self.created_at or datetime.now(timezone.utc).isoformat(),
        }
    
    def get_attribution(self) -> str:
        """Generiert Attribution-Text"""
        if self.is_fallback:
            return f"Foto: {self.author} / {self.license_name}"
        
        if not self.author or not self.license_name:
            return ""
        
        return f"Foto: {self.author} / Wikimedia Commons / {self.license_name}"


# =============================================================================
# SPIELER-ERKENNUNG
# =============================================================================

class PlayerDetector:
    """Erkennt Spielernamen aus Artikeltext"""
    
    # Muster für typische Spielernamen (Vorname Nachname)
    # Unterstützt: Akzente (é, á, ñ, etc.), Umlaute (ä, ö, ü), Bindestriche
    NAME_PATTERN = re.compile(
        r'\b([A-ZÄÖÜÉÈÊÁÀÂÍÌÎÓÒÔÚÙÛÑÇ][a-zäöüßéèêëáàâãíìîïóòôõúùûñç]+'
        r'(?:\s+(?:de|van|von|der|dos|da|di|el|la|del))?'
        r'\s+[A-ZÄÖÜÉÈÊÁÀÂÍÌÎÓÒÔÚÙÛÑÇ][a-zäöüßéèêëáàâãíìîïóòôõúùûñç]+'
        r'(?:-[A-ZÄÖÜÉÈÊÁÀÂÍÌÎÓÒÔÚÙÛÑÇ][a-zäöüßéèêëáàâãíìîïóòôõúùûñç]+)?)\b'
    )
    
    def detect_player(self, title: str, body: str) -> Optional[str]:
        """
        Erkennt den wichtigsten Spieler aus Titel und Text.
        
        Priorität:
        1. Name im Titel
        2. Häufigster Name im Text
        """
        # 1. Suche im Titel (höchste Priorität)
        title_player = self._find_player_in_text(title)
        if title_player:
            logger.info(f"[PLAYER] Found in title: {title_player}")
            return title_player
        
        # 2. Suche im Body
        body_player = self._find_most_frequent_player(body)
        if body_player:
            logger.info(f"[PLAYER] Found in body: {body_player}")
            return body_player
        
        logger.info("[PLAYER] No player detected")
        return None
    
    def _find_player_in_text(self, text: str) -> Optional[str]:
        """Findet ersten validen Spielernamen im Text"""
        matches = self.NAME_PATTERN.findall(text)
        
        for match in matches:
            name = match.strip()
            if self._is_valid_player_name(name):
                return name
        
        return None
    
    def _find_most_frequent_player(self, text: str) -> Optional[str]:
        """Findet häufigsten Spielernamen im Text"""
        matches = self.NAME_PATTERN.findall(text)
        
        # Zähle Vorkommen
        name_counts = {}
        for match in matches:
            name = match.strip()
            if self._is_valid_player_name(name):
                name_counts[name] = name_counts.get(name, 0) + 1
        
        if not name_counts:
            return None
        
        # Sortiere nach Häufigkeit
        sorted_names = sorted(name_counts.items(), key=lambda x: -x[1])
        return sorted_names[0][0]
    
    def _is_valid_player_name(self, name: str) -> bool:
        """Prüft ob ein Name ein valider Spielername ist"""
        if not name or len(name) < 5:
            return False
        
        # Muss aus mind. 2 Teilen bestehen
        parts = name.split()
        if len(parts) < 2:
            return False
        
        # Keine ignorierten Begriffe
        name_lower = name.lower()
        for term in IGNORED_TERMS:
            if term in name_lower:
                return False
        
        # Jeder Teil muss mit Großbuchstaben beginnen
        for part in parts:
            if part.lower() in ["de", "van", "von", "der", "dos", "da", "di"]:
                continue
            if not part[0].isupper():
                return False
        
        return True


# =============================================================================
# WIKIMEDIA COMMONS API
# =============================================================================

class WikimediaSearcher:
    """Sucht Bilder auf Wikimedia Commons"""
    
    SEARCH_API = "https://commons.wikimedia.org/w/api.php"
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=15)
        self.headers = {
            "User-Agent": "TransferNewsDe/1.0 (https://transfernews.de; contact@transfernews.de)",
        }
        self.cache = {}
    
    async def search_player_image(self, player_name: str) -> List[WikimediaImage]:
        """
        Sucht nach Bildern eines Spielers.
        Probiert mehrere Suchvarianten.
        """
        # Cache prüfen
        cache_key = player_name.lower()
        if cache_key in self.cache:
            logger.debug(f"[WIKIMEDIA] Cache hit: {player_name}")
            return self.cache[cache_key]
        
        # Suchvarianten
        search_variants = [
            player_name,
            f"{player_name} footballer",
            f"{player_name} football",
            f"{player_name} soccer",
            f"{player_name} 2024",
            f"{player_name} 2023",
        ]
        
        all_images = []
        seen_urls = set()
        
        for variant in search_variants:
            images = await self._search(variant)
            for img in images:
                if img.url not in seen_urls:
                    seen_urls.add(img.url)
                    all_images.append(img)
            
            # Wenn wir genug haben, stoppen
            if len(all_images) >= 10:
                break
        
        # Score berechnen und sortieren
        for img in all_images:
            img.quality_score = self._calculate_score(img, player_name)
        
        all_images.sort(key=lambda x: -x.quality_score)
        
        # Cachen
        self.cache[cache_key] = all_images[:10]
        
        return all_images[:10]
    
    async def _search(self, query: str, limit: int = 5) -> List[WikimediaImage]:
        """Führt eine Wikimedia Commons Suche durch"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                # Schritt 1: Suche nach Dateien
                params = {
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": f"filetype:bitmap {query}",
                    "gsrnamespace": "6",  # File namespace
                    "gsrlimit": str(limit),
                    "prop": "imageinfo",
                    "iiprop": "url|size|extmetadata",
                    "iiurlwidth": "1200",
                }
                
                async with session.get(self.SEARCH_API, params=params) as response:
                    if response.status != 200:
                        return []
                    
                    data = await response.json()
                    pages = data.get("query", {}).get("pages", {})
                    
                    images = []
                    for page_id, page in pages.items():
                        img = self._parse_image(page, query)
                        if img:
                            images.append(img)
                    
                    return images
                    
        except Exception as e:
            logger.error(f"[WIKIMEDIA] Search error: {e}")
            return []
    
    def _parse_image(self, page: dict, search_term: str) -> Optional[WikimediaImage]:
        """Parst Wikimedia API Response zu WikimediaImage"""
        try:
            info = page.get("imageinfo", [{}])[0]
            meta = info.get("extmetadata", {})
            
            url = info.get("thumburl") or info.get("url", "")
            width = info.get("thumbwidth") or info.get("width", 0)
            height = info.get("thumbheight") or info.get("height", 0)
            
            # Lizenz
            license_name = meta.get("LicenseShortName", {}).get("value", "")
            license_url = meta.get("LicenseUrl", {}).get("value", "")
            
            # Autor
            author_raw = meta.get("Artist", {}).get("value", "")
            # HTML aus Author extrahieren
            author = re.sub(r'<[^>]+>', '', author_raw).strip()
            author = author[:100]  # Begrenzen
            
            # Quell-URL
            source_url = info.get("descriptionurl", "")
            
            title = page.get("title", "").replace("File:", "")
            
            return WikimediaImage(
                url=url,
                width=width,
                height=height,
                title=title,
                license_name=license_name,
                license_url=license_url,
                author=author,
                author_url="",
                source_url=source_url,
                search_term=search_term,
            )
            
        except Exception as e:
            logger.debug(f"[WIKIMEDIA] Parse error: {e}")
            return None
    
    def _calculate_score(self, img: WikimediaImage, player_name: str) -> int:
        """Berechnet Quality-Score (0-100)"""
        score = 50  # Basis
        
        # Größe (+/- 20)
        if img.width >= 1200:
            score += 20
        elif img.width >= 800:
            score += 10
        elif img.width < 600:
            score -= 20
        
        # Seitenverhältnis (+/- 10)
        if img.width > 0 and img.height > 0:
            ratio = img.width / img.height
            if 1.3 < ratio < 2.0:  # Nahe 16:9
                score += 10
            elif ratio < 0.8 or ratio > 2.5:  # Extrem
                score -= 10
        
        # Lizenz (+/- 15)
        license_lower = img.license_name.lower().replace(" ", "").replace("-", "")
        
        # Normalisierte Lizenz-Checks
        is_valid_license = False
        
        # CC-BY-SA (alle Versionen)
        if "ccbysa" in license_lower or "ccbysam" in license_lower:
            is_valid_license = True
        # CC-BY (alle Versionen)
        elif "ccby" in license_lower and "nc" not in license_lower:  # Exclude CC-BY-NC
            is_valid_license = True
        # CC0 / Public Domain
        elif "cc0" in license_lower or "publicdomain" in license_lower or license_lower.startswith("pd"):
            is_valid_license = True
        # GFDL
        elif "gfdl" in license_lower:
            is_valid_license = True
        # Attribution nur
        elif "attribution" in license_lower:
            is_valid_license = True
        
        if is_valid_license:
            score += 15
            img.is_valid = True
        else:
            score -= 30
            img.is_valid = False
            img.rejection_reason = f"Ungeeignete Lizenz: {img.license_name}"
        
        # Name im Titel (+15)
        title_lower = img.title.lower()
        name_parts = player_name.lower().split()
        if all(part in title_lower for part in name_parts):
            score += 15
        elif any(part in title_lower for part in name_parts):
            score += 5
        
        # Negative Signale
        negative_terms = ["logo", "wappen", "crest", "badge", "poster", 
                         "collage", "screenshot", "icon", "flag", "map"]
        if any(term in title_lower for term in negative_terms):
            score -= 30
            img.is_valid = False
            img.rejection_reason = "Logo/Grafik erkannt"
        
        # Gruppen-Signale
        group_terms = ["team", "squad", "mannschaft", "group", "national"]
        if any(term in title_lower for term in group_terms):
            score -= 15
        
        # Autor vorhanden (+5)
        if img.author and len(img.author) > 2:
            score += 5
        else:
            img.is_valid = False
            img.rejection_reason = "Kein Autor"
        
        return max(0, min(100, score))


# =============================================================================
# ARTIKEL-BILD-SERVICE
# =============================================================================

class ArticleImageService:
    """
    Hauptservice für Artikelbilder.
    Koordiniert Erkennung, Suche, Bewertung und Speicherung.
    """
    
    MIN_QUALITY_SCORE = 50
    
    def __init__(self, db=None):
        self.db = db
        self.player_detector = PlayerDetector()
        self.searcher = WikimediaSearcher()
    
    async def process_article(self, article: dict) -> ArticleImage:
        """
        Verarbeitet einen Artikel und findet passendes Bild.
        
        Returns:
            ArticleImage mit allen Metadaten
        """
        title = article.get("title", "")
        body = article.get("body", "")
        article_id = article.get("id", "")
        
        logger.info(f"[IMAGE] Processing: {title[:50]}...")
        
        # Schritt 1: Spieler erkennen
        player = self.player_detector.detect_player(title, body)
        
        if not player:
            # Kein Spieler erkannt -> Fallback
            logger.info(f"[IMAGE] No player detected, using fallback")
            return self._create_fallback("stadium", ImageStatus.NO_PLAYER, "", "Kein Spieler erkannt")
        
        # Schritt 2: Wikimedia-Suche
        images = await self.searcher.search_player_image(player)
        
        if not images:
            logger.info(f"[IMAGE] No results for: {player}")
            return self._create_fallback("football", ImageStatus.NO_RESULTS, player, "Keine Treffer")
        
        # Schritt 3: Bestes valides Bild finden
        best_image = None
        for img in images:
            if img.is_valid and img.quality_score >= self.MIN_QUALITY_SCORE:
                # Zusätzliche Prüfungen
                if img.width < MIN_WIDTH:
                    continue
                if not img.license_name:
                    continue
                if not img.author:
                    continue
                
                best_image = img
                break
        
        if not best_image:
            # Kein passendes Bild
            reason = images[0].rejection_reason if images else "Alle Treffer ungeeignet"
            logger.info(f"[IMAGE] No suitable image for: {player}, reason: {reason}")
            return self._create_fallback("football", ImageStatus.LOW_QUALITY, player, reason)
        
        # Schritt 4: ArticleImage erstellen
        logger.info(f"[IMAGE] Found image for {player}: {best_image.title[:50]}... (score={best_image.quality_score})")
        
        return ArticleImage(
            url=best_image.url,
            width=best_image.width,
            height=best_image.height,
            status=ImageStatus.FOUND,
            license_name=best_image.license_name,
            license_url=best_image.license_url,
            author=best_image.author,
            author_url=best_image.author_url,
            source_url=best_image.source_url,
            search_term=best_image.search_term,
            detected_player=player,
            quality_score=best_image.quality_score,
            is_fallback=False,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    
    def _create_fallback(
        self, 
        category: str, 
        status: ImageStatus, 
        player: str, 
        reason: str
    ) -> ArticleImage:
        """Erstellt ein Fallback-Bild"""
        fallback = FALLBACK_IMAGES.get(category, FALLBACK_IMAGES["stadium"])
        
        return ArticleImage(
            url=fallback["url"],
            width=1200,
            height=675,
            status=status,
            license_name=fallback["license"],
            author=fallback["attribution"],
            detected_player=player,
            error_reason=reason,
            is_fallback=True,
            fallback_category=category,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    
    async def update_article_image(self, article_id: str, image: ArticleImage) -> bool:
        """Speichert Bild-Metadaten zum Artikel"""
        if self.db is None:
            return False
        
        try:
            await self.db.articles.update_one(
                {"id": article_id},
                {
                    "$set": {
                        "hero_image": image.url,
                        "hero_image_width": image.width,
                        "hero_image_height": image.height,
                        "hero_image_meta": image.to_dict(),
                        "hero_image_source": "wikimedia" if not image.is_fallback else "fallback",
                        "og_image": image.url,
                    }
                }
            )
            return True
        except Exception as e:
            logger.error(f"[IMAGE] Update error: {e}")
            return False
    
    async def search_and_update(self, article: dict) -> ArticleImage:
        """Sucht Bild und aktualisiert Artikel"""
        image = await self.process_article(article)
        
        if self.db is not None and article.get("id"):
            await self.update_article_image(article["id"], image)
        
        return image
    
    async def manual_search(self, article_id: str, search_term: str) -> List[WikimediaImage]:
        """Manuelle Suche für Admin"""
        return await self.searcher.search_player_image(search_term)
    
    async def set_manual_image(self, article_id: str, image_data: dict) -> bool:
        """Setzt manuell ein Bild (für Admin)"""
        if self.db is None:
            return False
        
        image = ArticleImage(
            url=image_data.get("url", ""),
            width=image_data.get("width", 1200),
            height=image_data.get("height", 675),
            status=ImageStatus.MANUAL,
            license_name=image_data.get("license_name", ""),
            license_url=image_data.get("license_url", ""),
            author=image_data.get("author", ""),
            source_url=image_data.get("source_url", ""),
            search_term=image_data.get("search_term", ""),
            detected_player=image_data.get("player", ""),
            is_fallback=False,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        
        return await self.update_article_image(article_id, image)
    
    async def use_fallback(self, article_id: str, category: str = "stadium") -> bool:
        """Setzt Fallback-Bild für Artikel"""
        image = self._create_fallback(category, ImageStatus.FALLBACK, "", "Manuell Fallback gewählt")
        return await self.update_article_image(article_id, image)


# =============================================================================
# FACTORY
# =============================================================================

_service = None

def get_article_image_service(db=None) -> ArticleImageService:
    global _service
    if _service is None or db is not None:
        _service = ArticleImageService(db)
    return _service
