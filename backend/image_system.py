"""
TransferNews.de - IMAGE SYSTEM für Google Discover
===================================================

Verwaltet hochauflösende Bilder (≥1200px) für:
- Google Discover Optimierung
- og:image Meta-Tags
- Twitter Card Images
- Article Hero Images

Quellen:
- Unsplash (Stadion/Fußball-Bilder)
- Fallback: Generierte Placeholder
"""

import hashlib
import logging
import os
import aiohttp
import asyncio
from typing import Optional, Dict, List
from datetime import datetime, timezone

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
# IMAGE SELECTOR
# =============================================================================

class ImageSelector:
    """Wählt das beste Bild für einen Artikel basierend auf Entitäten"""
    
    def __init__(self):
        self.image_cache = {}
    
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
