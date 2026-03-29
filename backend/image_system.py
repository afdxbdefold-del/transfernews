"""
TransferNews.de - IMAGE SYSTEM für Google Discover
===================================================

Verwaltet hochauflösende Bilder (≥1200px) für:
- Google Discover Optimierung
- og:image Meta-Tags
- Twitter Card Images
- Article Hero Images

Quellen (Priorität):
1. RSS-Feed Bilder (wenn ≥1200px)
2. Unsplash Suche nach Spieler/Club
3. Club-/Liga-spezifische Fallbacks
4. Generische Fußball-Bilder
"""

import hashlib
import logging
import os
import aiohttp
import asyncio
import re
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timezone
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

# =============================================================================
# BILDKONFIGURATION
# =============================================================================

# Google Discover empfiehlt mindestens 1200px Breite
MIN_WIDTH = 1200
MIN_HEIGHT = 675  # 16:9 Ratio

# Fallback-Bilder nach Kategorie
FALLBACK_IMAGES = {
    "transfer": "/images/fallback/transfer-hero.jpg",
    "bundesliga": "/images/fallback/bundesliga-hero.jpg",
    "premier_league": "/images/fallback/premier-league-hero.jpg",
    "la_liga": "/images/fallback/la-liga-hero.jpg",
    "serie_a": "/images/fallback/serie-a-hero.jpg",
    "champions_league": "/images/fallback/champions-league-hero.jpg",
    "default": "/images/fallback/football-hero.jpg",
}

# Club-spezifische Bildpfade (hochauflösend)
CLUB_IMAGES = {
    "Real Madrid": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=1200",
    "FC Barcelona": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=1200",
    "FC Bayern München": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=1200",
    "Borussia Dortmund": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=1200",
    "Manchester City": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=1200",
    "FC Liverpool": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=1200",
    "FC Chelsea": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=1200",
    "FC Arsenal": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=1200",
    "Manchester United": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=1200",
    "Paris Saint-Germain": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=1200",
    "Juventus Turin": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=1200",
}

# Liga-spezifische Bilder
LEAGUE_IMAGES = {
    "Bundesliga": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=1200",
    "Premier League": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=1200",
    "La Liga": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=1200",
    "Serie A": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=1200",
    "Ligue 1": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=1200",
    "Champions League": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=1200",
}

# Allgemeine Fußball-Bilder für Fallback
GENERIC_FOOTBALL_IMAGES = [
    "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=1200",
    "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=1200",
    "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=1200",
    "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=1200",
    "https://images.unsplash.com/photo-1518604666860-9ed391f76460?w=1200",
    "https://images.unsplash.com/photo-1459865264687-595d652de67e?w=1200",
]


# =============================================================================
# IMAGE VALIDATOR & FETCHER
# =============================================================================

class ImageValidator:
    """Prüft und validiert Bildgrößen für Google Discover"""
    
    @staticmethod
    async def check_image_size(url: str, timeout: int = 5) -> Tuple[bool, int, int]:
        """
        Prüft ob ein Bild die Mindestgröße für Google Discover erfüllt.
        
        Returns:
            (is_valid, width, height)
        """
        if not url or not url.startswith(('http://', 'https://')):
            return (False, 0, 0)
        
        # Überspringe Video-URLs
        if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '.webm', '.mov']):
            return (False, 0, 0)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status != 200:
                        return (False, 0, 0)
                    
                    content_type = response.headers.get('content-type', '')
                    if 'image' not in content_type:
                        return (False, 0, 0)
                    
                    # Lade nur die ersten Bytes für Header-Info
                    data = await response.read()
                    
                    try:
                        img = Image.open(BytesIO(data))
                        width, height = img.size
                        is_valid = width >= MIN_WIDTH and height >= MIN_HEIGHT
                        logger.debug(f"[IMAGE] {url[:50]}... → {width}x{height} (valid: {is_valid})")
                        return (is_valid, width, height)
                    except Exception as e:
                        logger.debug(f"[IMAGE] Could not parse image: {e}")
                        return (False, 0, 0)
                        
        except Exception as e:
            logger.debug(f"[IMAGE] Error checking {url[:50]}...: {e}")
            return (False, 0, 0)
    
    @staticmethod
    def extract_size_from_url(url: str) -> Tuple[int, int]:
        """
        Extrahiert Bildgröße aus URL-Parametern (z.B. ?w=1200 oder _w520)
        
        Returns:
            (width, height) oder (0, 0) wenn nicht erkennbar
        """
        # Pattern: w=1200, width=1200, _w1200, /1200x800
        patterns = [
            r'[?&]w=(\d+)',
            r'[?&]width=(\d+)',
            r'_w(\d+)',
            r'/(\d{3,4})x(\d{3,4})',
            r'w(\d+)_',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    return (int(groups[0]), int(groups[1]))
                elif len(groups) == 1:
                    width = int(groups[0])
                    # Schätze Höhe basierend auf 16:9
                    return (width, int(width * 9 / 16))
        
        return (0, 0)
    
    @staticmethod
    def upgrade_image_url(url: str, target_width: int = 1200) -> str:
        """
        Versucht eine Bild-URL auf höhere Auflösung zu upgraden.
        Unterstützt gängige CDN-Formate.
        """
        if not url:
            return url
        
        # Unsplash: ?w=XXX durch ?w=1200 ersetzen
        if 'unsplash.com' in url:
            url = re.sub(r'\?w=\d+', f'?w={target_width}', url)
            if '?w=' not in url:
                url += f'?w={target_width}'
            return url
        
        # Spiegel CDN: _w520 durch _w1200 ersetzen
        if 'spiegel.de' in url:
            url = re.sub(r'_w\d+', f'_w{target_width}', url)
            return url
        
        # Zeit.de: /original__640x360 durch /original ersetzen
        if 'zeit.de' in url:
            url = re.sub(r'/original__\d+x\d+', '/original', url)
            return url
        
        # Generisch: Versuche Größenparameter zu ersetzen
        url = re.sub(r'([?&])w=\d+', f'\\1w={target_width}', url)
        url = re.sub(r'([?&])width=\d+', f'\\1width={target_width}', url)
        
        return url


# =============================================================================
# IMAGE SELECTOR
# =============================================================================

class ImageSelector:
    """Wählt das beste Bild für einen Artikel basierend auf Entitäten"""
    
    def __init__(self):
        self.image_cache = {}
        self.validator = ImageValidator()
    
    async def get_best_image(
        self,
        rss_image_url: Optional[str] = None,
        player_name: Optional[str] = None,
        club_name: Optional[str] = None,
        league: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Findet das beste Bild mit Priorität:
        1. RSS-Feed Bild (wenn ≥1200px)
        2. Upgraded RSS-Feed Bild
        3. Club-spezifisches Fallback
        4. Liga-spezifisches Fallback
        5. Generisches Fußball-Bild
        """
        
        # Priorität 1: RSS-Bild prüfen
        if rss_image_url:
            # Versuche URL zu upgraden
            upgraded_url = self.validator.upgrade_image_url(rss_image_url)
            
            # Schnelle Größenschätzung aus URL
            est_width, est_height = self.validator.extract_size_from_url(upgraded_url)
            
            if est_width >= MIN_WIDTH:
                logger.info(f"[IMAGE] Using upgraded RSS image: {upgraded_url[:60]}...")
                return {
                    "url": upgraded_url,
                    "width": est_width,
                    "height": est_height or MIN_HEIGHT,
                    "alt": f"Transfer-News: {player_name or 'Spieler'}",
                    "source": "rss_upgraded"
                }
            
            # Vollständige Prüfung (langsamer, aber genauer)
            is_valid, width, height = await self.validator.check_image_size(upgraded_url)
            if is_valid:
                logger.info(f"[IMAGE] RSS image valid ({width}x{height}): {upgraded_url[:60]}...")
                return {
                    "url": upgraded_url,
                    "width": width,
                    "height": height,
                    "alt": f"Transfer-News: {player_name or 'Spieler'}",
                    "source": "rss"
                }
        
        # Fallback zu statischen Bildern
        return self.get_image_for_article(player_name, club_name, league)
    
    def get_image_for_article(
        self,
        player_name: Optional[str] = None,
        club_name: Optional[str] = None,
        league: Optional[str] = None,
        transfer_status: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Findet das beste Bild für einen Artikel.
        
        Returns:
            {
                "url": "https://...",
                "width": 1200,
                "height": 675,
                "alt": "Beschreibung",
                "source": "club|league|generic"
            }
        """
        # Priorität 1: Club-spezifisches Bild
        if club_name and club_name in CLUB_IMAGES:
            return {
                "url": CLUB_IMAGES[club_name],
                "width": MIN_WIDTH,
                "height": MIN_HEIGHT,
                "alt": f"Transfer-News: {player_name or 'Spieler'} und {club_name}",
                "source": "club"
            }
        
        # Priorität 2: Liga-spezifisches Bild
        if league and league in LEAGUE_IMAGES:
            return {
                "url": LEAGUE_IMAGES[league],
                "width": MIN_WIDTH,
                "height": MIN_HEIGHT,
                "alt": f"Transfer-News aus der {league}",
                "source": "league"
            }
        
        # Priorität 3: Deterministisches generisches Bild basierend auf Spieler-/Club-Name
        seed = hashlib.md5(f"{player_name or ''}{club_name or ''}".encode()).hexdigest()
        index = int(seed[:8], 16) % len(GENERIC_FOOTBALL_IMAGES)
        
        return {
            "url": GENERIC_FOOTBALL_IMAGES[index],
            "width": MIN_WIDTH,
            "height": MIN_HEIGHT,
            "alt": f"Fußball Transfer-News: {player_name or 'Aktuell'}",
            "source": "generic"
        }
    
    def generate_og_tags(self, article: dict) -> Dict[str, str]:
        """
        Generiert Open Graph Tags für einen Artikel.
        Optimiert für Google Discover.
        """
        image_data = self.get_image_for_article(
            player_name=article.get("player_name"),
            club_name=article.get("club_name"),
            league=article.get("league"),
            transfer_status=article.get("transfer_status")
        )
        
        return {
            "og:image": image_data["url"],
            "og:image:width": str(image_data["width"]),
            "og:image:height": str(image_data["height"]),
            "og:image:alt": image_data["alt"],
            "og:image:type": "image/jpeg",
            "twitter:card": "summary_large_image",
            "twitter:image": image_data["url"],
        }


# =============================================================================
# IMAGE METADATA SERVICE
# =============================================================================

class ImageMetadataService:
    """
    Speichert Bild-Metadaten in der Datenbank.
    Ermöglicht spätere Analyse und Optimierung.
    """
    
    def __init__(self, db):
        self.db = db
        self.selector = ImageSelector()
    
    async def assign_image_to_article(self, article_id: str, article_data: dict) -> dict:
        """
        Weist einem Artikel ein optimiertes Bild zu.
        Speichert Metadaten in der DB.
        """
        image_data = self.selector.get_image_for_article(
            player_name=article_data.get("player_name"),
            club_name=article_data.get("club_name"),
            league=article_data.get("league"),
            transfer_status=article_data.get("transfer_status")
        )
        
        og_tags = self.selector.generate_og_tags(article_data)
        
        # Update Artikel mit Bild-Metadaten
        await self.db.articles.update_one(
            {"id": article_id},
            {
                "$set": {
                    "hero_image": image_data["url"],
                    "hero_image_width": image_data["width"],
                    "hero_image_height": image_data["height"],
                    "hero_image_alt": image_data["alt"],
                    "hero_image_source": image_data["source"],
                    "og_image": og_tags["og:image"],
                    "og_image_width": og_tags["og:image:width"],
                    "og_image_height": og_tags["og:image:height"],
                    "image_assigned_at": datetime.now(timezone.utc).isoformat(),
                }
            }
        )
        
        logger.info(f"[IMAGE] Assigned {image_data['source']} image to article {article_id[:8]}")
        
        return image_data
    
    async def update_missing_images(self, limit: int = 50) -> dict:
        """
        Aktualisiert Artikel ohne Bilder.
        Für Batch-Processing.
        """
        result = {"updated": 0, "errors": 0}
        
        # Finde Artikel ohne hero_image
        articles = await self.db.articles.find(
            {"hero_image": {"$exists": False}},
            {"_id": 0, "id": 1, "player_name": 1, "club_name": 1, "league": 1, "transfer_status": 1}
        ).limit(limit).to_list(limit)
        
        for article in articles:
            try:
                await self.assign_image_to_article(article["id"], article)
                result["updated"] += 1
            except Exception as e:
                logger.error(f"[IMAGE] Error updating article {article.get('id')}: {e}")
                result["errors"] += 1
        
        return result


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def get_image_selector() -> ImageSelector:
    """Returns singleton ImageSelector"""
    return ImageSelector()


async def create_image_service(db) -> ImageMetadataService:
    """Factory für ImageMetadataService"""
    return ImageMetadataService(db)
