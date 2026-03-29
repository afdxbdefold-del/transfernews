"""
TransferNews.de - SPEED-OPTIMIZED NEWS PIPELINE
================================================

FLOW:
RSS → Event → Sofort-Artikel (30s) → GPT-Rewrite (async) → Update

ZIELE:
- Artikel in < 30 Sekunden live
- Google crawlt schneller
- Weniger AI-Signale
- Discover-optimiert
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import os

logger = logging.getLogger(__name__)


# =============================================================================
# TEMPLATE-BASIERTE SOFORT-ARTIKEL (KEIN GPT!)
# =============================================================================

class InstantArticleGenerator:
    """
    Generiert Artikel SOFORT ohne GPT.
    Template-basiert für maximale Geschwindigkeit.
    """
    
    # Transfer-Status Templates
    STATUS_TEMPLATES = {
        "official": {
            "de": {
                "prefix": "OFFIZIELL:",
                "lead": "{player} wechselt zu {club}. Der Transfer wurde offiziell bestätigt.",
                "status": "OFFIZIELL",
                "probability": 100
            },
            "en": {
                "prefix": "OFFICIAL:",
                "lead": "{player} joins {club}. The transfer has been officially confirmed.",
                "status": "OFFIZIELL",
                "probability": 100
            }
        },
        "confirmed": {
            "de": {
                "prefix": "BESTÄTIGT:",
                "lead": "{player} steht vor einem Wechsel zu {club}. Eine Einigung wurde erzielt.",
                "status": "BESTÄTIGT",
                "probability": 85
            },
            "en": {
                "prefix": "CONFIRMED:",
                "lead": "{player} is set to join {club}. An agreement has been reached.",
                "status": "BESTÄTIGT",
                "probability": 85
            }
        },
        "advanced": {
            "de": {
                "prefix": "VERHANDLUNGEN:",
                "lead": "{player} und {club} befinden sich in fortgeschrittenen Verhandlungen.",
                "status": "VERHANDLUNG",
                "probability": 70
            },
            "en": {
                "prefix": "NEGOTIATIONS:",
                "lead": "{player} and {club} are in advanced negotiations.",
                "status": "VERHANDLUNG",
                "probability": 70
            }
        },
        "rumour": {
            "de": {
                "prefix": "GERÜCHT:",
                "lead": "{player} wird mit {club} in Verbindung gebracht.",
                "status": "GERÜCHT",
                "probability": 40
            },
            "en": {
                "prefix": "RUMOUR:",
                "lead": "{player} is being linked with {club}.",
                "status": "GERÜCHT",
                "probability": 40
            }
        }
    }
    
    # Body Templates (kurz, faktisch, kein AI-Smell, OHNE Markdown)
    BODY_TEMPLATES = {
        "official": """{source_name} berichtet: {headline}

{player} wechselt zu {club}. Der Transfer wurde offiziell bestätigt.

Laut {source_name} ist der Deal abgeschlossen. Details zu Ablöse und Vertragslaufzeit wurden noch nicht bekannt gegeben.

Der Wechsel stärkt den Kader von {club}. {player} soll das Team verstärken.""",

        "confirmed": """{source_name} meldet: {headline}

{player} und {club} haben sich geeinigt. Die offizielle Bestätigung steht noch aus.

Die Verhandlungen sind abgeschlossen. Der Transfer soll zeitnah verkündet werden.

Für {club} bedeutet die Verpflichtung eine wichtige Verstärkung.""",

        "advanced": """{source_name} berichtet: {headline}

{player} befindet sich in Gesprächen mit {club}. Ein Wechsel gilt als wahrscheinlich.

Die Verhandlungen sind weit fortgeschritten. Beide Seiten arbeiten an einer Einigung.

Eine Entscheidung wird zeitnah erwartet.""",

        "rumour": """{source_name} meldet: {headline}

{player} wird mit einem Wechsel zu {club} in Verbindung gebracht. Konkrete Verhandlungen sind bisher nicht bestätigt.

Das Interesse von {club} an {player} soll laut Berichten bestehen. Offizielle Stellungnahmen gibt es noch nicht.

Ob es zu konkreten Gesprächen kommt, ist derzeit offen."""
    }
    
    def __init__(self):
        self.player_cache = {}
        self.club_cache = {}
    
    def detect_transfer_status(self, headline: str) -> str:
        """Erkennt Transfer-Status aus Headline"""
        headline_lower = headline.lower()
        
        # Official keywords
        if any(kw in headline_lower for kw in [
            "offiziell", "official", "done deal", "here we go",
            "confirmed", "bestätigt", "fix", "perfekt", "unterschrieben",
            "signed", "joins", "verpflichtet"
        ]):
            return "official"
        
        # Confirmed/Agreement keywords
        if any(kw in headline_lower for kw in [
            "einigung", "agreement", "deal", "agrees terms",
            "personal terms", "medical", "abschluss"
        ]):
            return "confirmed"
        
        # Advanced negotiations
        if any(kw in headline_lower for kw in [
            "verhandlung", "negotiations", "talks", "close to",
            "kurz vor", "bald", "soon"
        ]):
            return "advanced"
        
        # Default: Rumour
        return "rumour"
    
    def extract_entities(self, headline: str, body: str = "") -> Dict[str, any]:
        """
        Extrahiert Spieler und Club aus Text.
        Nutzt die erweiterte entity_recognition.py für bessere Ergebnisse.
        """
        try:
            from entity_recognition import get_entity_recognizer
            recognizer = get_entity_recognizer()
            
            text = f"{headline} {body}"
            result = recognizer.recognize_all(text)
            
            player_match = result.get("player")
            club_match = result.get("to_club")
            from_club_match = result.get("from_club")
            
            player = player_match.canonical_name if player_match else "Unbekannter Spieler"
            club = club_match.canonical_name if club_match else "Unbekannter Verein"
            from_club = from_club_match.canonical_name if from_club_match else None
            
            # Zusätzliche Metadaten für Bilder und SEO
            player_metadata = player_match.metadata if player_match else {}
            club_metadata = club_match.metadata if club_match else {}
            
            return {
                "player": player,
                "club": club,
                "from_club": from_club,
                "transfer_type": result.get("transfer_type", "unknown"),
                "confidence": result.get("confidence", 0.3),
                "player_position": player_metadata.get("position"),
                "player_nationality": player_metadata.get("nationality"),
                "player_popularity": player_metadata.get("popularity", 50),
                "club_country": club_metadata.get("country"),
                "club_league": club_metadata.get("league"),
                "club_popularity": club_metadata.get("popularity", 50),
            }
        except Exception as e:
            logger.warning(f"[ENTITY] Fallback to simple extraction: {e}")
            # Fallback zur einfachen Extraktion
            return self._simple_extract_entities(headline, body)
    
    def _simple_extract_entities(self, headline: str, body: str = "") -> Dict[str, str]:
        """Fallback: Einfache Entity-Extraktion"""
        text = f"{headline} {body}".lower()
        
        KNOWN_PLAYERS = {
            "mbappe": "Kylian Mbappé", "haaland": "Erling Haaland",
            "bellingham": "Jude Bellingham", "messi": "Lionel Messi",
            "ronaldo": "Cristiano Ronaldo", "salah": "Mohamed Salah",
            "kane": "Harry Kane", "musiala": "Jamal Musiala",
            "wirtz": "Florian Wirtz", "saka": "Bukayo Saka",
            "palmer": "Cole Palmer", "vinicius": "Vinícius Jr.",
            "pedri": "Pedri", "gavi": "Gavi", "yamal": "Lamine Yamal",
        }
        
        KNOWN_CLUBS = {
            "real madrid": "Real Madrid", "barcelona": "FC Barcelona",
            "bayern": "FC Bayern München", "dortmund": "Borussia Dortmund",
            "manchester city": "Manchester City", "liverpool": "FC Liverpool",
            "chelsea": "FC Chelsea", "arsenal": "FC Arsenal",
            "manchester united": "Manchester United", "psg": "Paris Saint-Germain",
        }
        
        player = "Unbekannter Spieler"
        club = "Unbekannter Verein"
        
        for key, name in KNOWN_PLAYERS.items():
            if key in text:
                player = name
                break
        
        for key, name in KNOWN_CLUBS.items():
            if key in text:
                club = name
                break
        
        return {"player": player, "club": club, "confidence": 0.5}
    
    def generate_title(self, event: dict) -> str:
        """Generiert SEO-optimierten Titel"""
        headline = event.get("headline_raw", "")
        entities = self.extract_entities(headline)
        status = self.detect_transfer_status(headline)
        
        player = entities["player"]
        club = entities["club"]
        
        # Titel-Templates
        if status == "official":
            if player != "Unbekannter Spieler" and club != "Unbekannter Verein":
                return f"{player} wechselt zu {club} – Transfer offiziell"
            return f"Transfer offiziell bestätigt: {headline[:50]}"
        
        elif status == "confirmed":
            if player != "Unbekannter Spieler" and club != "Unbekannter Verein":
                return f"{player} vor Wechsel zu {club} – Einigung erzielt"
            return f"Transfer-Einigung: {headline[:50]}"
        
        elif status == "advanced":
            if player != "Unbekannter Spieler" and club != "Unbekannter Verein":
                return f"{player}: Verhandlungen mit {club}"
            return f"Transfer-Verhandlungen: {headline[:50]}"
        
        else:  # rumour
            if player != "Unbekannter Spieler" and club != "Unbekannter Verein":
                return f"Gerücht: {player} zu {club}?"
            return f"Transfer-Gerücht: {headline[:50]}"
    
    def generate_slug(self, title: str) -> str:
        """Generiert URL-Slug aus Titel"""
        slug = title.lower()
        # Umlaute
        slug = slug.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        slug = slug.replace("ß", "ss")
        # Sonderzeichen entfernen
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        # Max 60 Zeichen
        return slug[:60]
    
    def generate_instant_article(self, event: dict) -> dict:
        """
        Generiert SOFORT einen Artikel ohne GPT.
        Dauert < 100ms.
        """
        headline = event.get("headline_raw", "")
        source_name = event.get("source_name", "Unbekannte Quelle")
        source_url = event.get("source_url", "")
        
        # Entitäten extrahieren
        entities = self.extract_entities(headline)
        player = entities["player"]
        club = entities["club"]
        
        # Status erkennen
        status = self.detect_transfer_status(headline)
        template = self.STATUS_TEMPLATES.get(status, self.STATUS_TEMPLATES["rumour"])
        
        # Titel generieren
        title = self.generate_title(event)
        slug = self.generate_slug(title)
        
        # Lead generieren
        lead_template = template["de"]["lead"]
        excerpt = lead_template.format(player=player, club=club)
        
        # Body generieren
        body_template = self.BODY_TEMPLATES.get(status, self.BODY_TEMPLATES["rumour"])
        timestamp = datetime.now(timezone.utc).strftime("%d.%m.%Y, %H:%M Uhr")
        
        body = body_template.format(
            headline=headline,
            player=player,
            club=club,
            source_name=source_name,
            timestamp=timestamp
        )
        
        return {
            "title": title,
            "slug": slug,
            "excerpt": excerpt,
            "body": body,
            "transfer_status": template["de"]["status"],
            "transfer_probability": template["de"]["probability"],
            "source_url": source_url,
            "source_name": source_name,
            "player_name": player,
            "club_name": club,
            "from_club": entities.get("from_club"),
            "player_position": entities.get("player_position"),
            "player_nationality": entities.get("player_nationality"),
            "club_league": entities.get("club_league"),
            "entity_confidence": entities.get("confidence", 0.5),
            "needs_gpt_rewrite": True,  # Markierung für async Rewrite
            "is_instant": True,
            "word_count": len(body.split()),
            "reading_time_minutes": max(1, len(body.split()) // 200),
        }


# =============================================================================
# DEDUPE SYSTEM (Player + Club + Type)
# =============================================================================

class DedupeSystem:
    """
    Verhindert Duplicate Content.
    Key: player + club + transfer_type
    """
    
    @staticmethod
    def generate_dedupe_key(player: str, club: str, transfer_type: str) -> str:
        """Generiert eindeutigen Dedupe-Key"""
        # Normalisieren
        player = player.lower().strip()
        club = club.lower().strip()
        transfer_type = transfer_type.lower().strip()
        
        content = f"{player}:{club}:{transfer_type}"
        return hashlib.md5(content.encode()).hexdigest()
    
    @staticmethod
    def generate_headline_key(headline: str, source: str) -> str:
        """Fallback: Headline-basierter Key"""
        content = f"{headline.lower()[:100]}:{source.lower()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    @staticmethod
    async def find_existing_article(db: AsyncIOMotorDatabase, dedupe_key: str) -> Optional[dict]:
        """Findet existierenden Artikel mit gleichem Key"""
        return await db.articles.find_one(
            {"dedupe_key": dedupe_key},
            {"_id": 0}
        )
    
    @staticmethod
    async def find_similar_article(db: AsyncIOMotorDatabase, player: str, club: str) -> Optional[dict]:
        """Findet ähnlichen Artikel (gleicher Spieler + Club)"""
        if player == "Unbekannter Spieler" or club == "Unbekannter Verein":
            return None
        
        # Suche nach Artikeln mit gleichem Spieler UND Club in letzten 48h
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        
        return await db.articles.find_one(
            {
                "player_name": player,
                "club_name": club,
                "published_at": {"$gte": cutoff}
            },
            {"_id": 0}
        )


# =============================================================================
# SPEED PIPELINE (Haupt-Logik)
# =============================================================================

class SpeedPipeline:
    """
    Optimierte Pipeline für schnelle News-Veröffentlichung.
    
    FLOW:
    1. RSS Event kommt rein
    2. Dedupe-Check (< 10ms)
    3. Instant-Artikel generieren (< 100ms)
    4. Sofort veröffentlichen
    5. Async: GPT-Rewrite queuen
    6. Async: Internal Links updaten
    7. Async: Sitemap updaten
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.instant_generator = InstantArticleGenerator()
        self.dedupe = DedupeSystem()
        self.gpt_queue = []  # Queue für GPT-Rewrites
    
    async def process_event(self, event: dict) -> dict:
        """
        Verarbeitet ein Event und erstellt sofort einen Artikel.
        
        Returns:
            {
                "action": "created" | "updated" | "skipped",
                "article_id": str | None,
                "time_ms": int
            }
        """
        start_time = datetime.now()
        
        headline = event.get("headline_raw", "")
        source_name = event.get("source_name", "")
        
        # 1. Entitäten extrahieren
        entities = self.instant_generator.extract_entities(headline)
        player = entities["player"]
        club = entities["club"]
        transfer_type = self.instant_generator.detect_transfer_status(headline)
        
        # 2. Dedupe-Key generieren
        dedupe_key = self.dedupe.generate_dedupe_key(player, club, transfer_type)
        
        # 3. Existierenden Artikel prüfen
        existing = await self.dedupe.find_existing_article(self.db, dedupe_key)
        
        if existing:
            # Update statt neu
            result = await self._update_existing_article(existing, event, transfer_type)
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            return {"action": "updated", "article_id": existing.get("id"), "time_ms": int(elapsed)}
        
        # 4. Ähnlichen Artikel prüfen (gleicher Spieler + Club)
        similar = await self.dedupe.find_similar_article(self.db, player, club)
        
        if similar:
            # Prüfen ob Status-Upgrade
            if self._should_upgrade_status(similar.get("transfer_status"), transfer_type):
                result = await self._upgrade_article_status(similar, event, transfer_type)
                elapsed = (datetime.now() - start_time).total_seconds() * 1000
                return {"action": "upgraded", "article_id": similar.get("id"), "time_ms": int(elapsed)}
            else:
                # Keine Änderung nötig
                elapsed = (datetime.now() - start_time).total_seconds() * 1000
                return {"action": "skipped", "article_id": similar.get("id"), "time_ms": int(elapsed)}
        
        # 5. Neuen Artikel erstellen (INSTANT!)
        article_data = self.instant_generator.generate_instant_article(event)
        article_data["dedupe_key"] = dedupe_key
        
        # 5b. Bild für Google Discover zuweisen - WIKIMEDIA SYSTEM (Priorität)
        try:
            from wikimedia_images import get_article_image_service
            
            # Wikimedia Service mit DB initialisieren
            image_service = get_article_image_service(self.db)
            
            # Artikel-Daten für Bildsuche vorbereiten
            article_for_image = {
                "title": article_data.get("title", ""),
                "body": article_data.get("body", ""),
            }
            
            # Wikimedia-Bild suchen
            wikimedia_result = await image_service.process_article(article_for_image)
            
            # Ergebnis zuweisen
            article_data["hero_image"] = wikimedia_result.url
            article_data["hero_image_width"] = wikimedia_result.width
            article_data["hero_image_height"] = wikimedia_result.height
            article_data["hero_image_alt"] = f"Transfer-News: {article_data.get('player_name', 'Spieler')}"
            article_data["hero_image_source"] = "wikimedia" if not wikimedia_result.is_fallback else "fallback"
            article_data["og_image"] = wikimedia_result.url
            
            # Wikimedia-spezifische Metadaten
            article_data["hero_image_meta"] = wikimedia_result.to_dict()
            
            source_type = "Wikimedia" if not wikimedia_result.is_fallback else "Fallback"
            logger.info(f"[IMAGE] Assigned {source_type} image (score={wikimedia_result.quality_score}): {wikimedia_result.url[:60]}...")
            
        except Exception as e:
            logger.warning(f"[IMAGE] Wikimedia system error: {e}")
            # Fallback zu altem System
            try:
                from image_system import get_image_selector
                selector = get_image_selector()
                image_data = selector.get_image_for_article(
                    player_name=article_data.get("player_name"),
                    club_name=article_data.get("club_name"),
                    league=article_data.get("club_league"),
                )
                article_data["hero_image"] = image_data["url"]
                article_data["hero_image_width"] = image_data["width"]
                article_data["hero_image_height"] = image_data["height"]
                article_data["hero_image_alt"] = image_data["alt"]
                article_data["hero_image_source"] = "legacy_fallback"
                article_data["og_image"] = image_data["url"]
            except Exception as e2:
                logger.error(f"[IMAGE] All image systems failed: {e2}")
        
        # 6. In DB speichern
        from models import generate_uuid
        article_id = generate_uuid()
        
        article = {
            "id": article_id,
            **article_data,
            "status": "published",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source_event_id": event.get("id"),
            "author_name": "transfernews.de",
        }
        
        await self.db.articles.insert_one(article)
        
        # 7. Event als verarbeitet markieren
        await self.db.events.update_one(
            {"id": event.get("id")},
            {"$set": {"status": "processed", "article_id": article_id}}
        )
        
        # 8. GPT-Rewrite queuen (async, später)
        self.gpt_queue.append(article_id)
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"[SPEED] Instant article created in {int(elapsed)}ms: {article_data['title'][:50]}")
        
        return {"action": "created", "article_id": article_id, "time_ms": int(elapsed)}
    
    def _should_upgrade_status(self, current_status: str, new_type: str) -> bool:
        """Prüft ob Status-Upgrade sinnvoll ist"""
        status_order = ["GERÜCHT", "VERHANDLUNG", "BESTÄTIGT", "OFFIZIELL"]
        type_to_status = {
            "rumour": "GERÜCHT",
            "advanced": "VERHANDLUNG",
            "confirmed": "BESTÄTIGT",
            "official": "OFFIZIELL"
        }
        
        new_status = type_to_status.get(new_type, "GERÜCHT")
        
        try:
            current_idx = status_order.index(current_status)
            new_idx = status_order.index(new_status)
            return new_idx > current_idx
        except ValueError:
            return False
    
    async def _update_existing_article(self, article: dict, event: dict, transfer_type: str) -> dict:
        """Aktualisiert existierenden Artikel mit neuen Infos"""
        headline = event.get("headline_raw", "")
        source_name = event.get("source_name", "")
        timestamp = datetime.now(timezone.utc).strftime("%d.%m.%Y, %H:%M Uhr")
        
        # Neuen Absatz hinzufügen
        update_text = f"\n\n## Update ({timestamp})\n\n{source_name} meldet: {headline}"
        
        new_body = article.get("body", "") + update_text
        
        await self.db.articles.update_one(
            {"id": article.get("id")},
            {
                "$set": {
                    "body": new_body,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "word_count": len(new_body.split()),
                }
            }
        )
        
        logger.info(f"[SPEED] Article updated: {article.get('title', '')[:50]}")
        return article
    
    async def _upgrade_article_status(self, article: dict, event: dict, new_type: str) -> dict:
        """Upgraded Artikel-Status (z.B. GERÜCHT → OFFIZIELL)"""
        type_to_status = {
            "rumour": "GERÜCHT",
            "advanced": "VERHANDLUNG",
            "confirmed": "BESTÄTIGT",
            "official": "OFFIZIELL"
        }
        
        type_to_prob = {
            "rumour": 40,
            "advanced": 70,
            "confirmed": 85,
            "official": 100
        }
        
        new_status = type_to_status.get(new_type, "GERÜCHT")
        new_prob = type_to_prob.get(new_type, 40)
        
        headline = event.get("headline_raw", "")
        source_name = event.get("source_name", "")
        timestamp = datetime.now(timezone.utc).strftime("%d.%m.%Y, %H:%M Uhr")
        
        # Status-Upgrade Text
        update_text = f"\n\n## STATUS-UPDATE: {new_status} ({timestamp})\n\n{source_name} bestätigt: {headline}"
        
        new_body = article.get("body", "") + update_text
        
        # Titel anpassen
        old_title = article.get("title", "")
        new_title = old_title.replace("Gerücht:", f"{new_status}:").replace("GERÜCHT:", f"{new_status}:")
        if "?" in new_title and new_status == "OFFIZIELL":
            new_title = new_title.replace("?", "!")
        
        await self.db.articles.update_one(
            {"id": article.get("id")},
            {
                "$set": {
                    "title": new_title,
                    "body": new_body,
                    "transfer_status": new_status,
                    "transfer_probability": new_prob,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "word_count": len(new_body.split()),
                }
            }
        )
        
        logger.info(f"[SPEED] Article upgraded to {new_status}: {new_title[:50]}")
        return article
    
    async def process_pending_events(self, limit: int = 20) -> dict:
        """Verarbeitet alle pending Events"""
        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "upgraded": 0,
            "skipped": 0,
            "total_time_ms": 0,
            "errors": []
        }
        
        # Pending Events laden
        events = await self.db.events.find(
            {"status": "pending"}
        ).sort("created_at", 1).limit(limit).to_list(limit)
        
        for event in events:
            try:
                res = await self.process_event(event)
                result["processed"] += 1
                result[res["action"]] = result.get(res["action"], 0) + 1
                result["total_time_ms"] += res["time_ms"]
            except Exception as e:
                logger.error(f"[SPEED] Error processing event: {e}")
                result["errors"].append(str(e))
                # Event trotzdem als fehlerhaft markieren
                await self.db.events.update_one(
                    {"id": event.get("id")},
                    {"$set": {"status": "error", "error": str(e)}}
                )
        
        if result["processed"] > 0:
            avg_time = result["total_time_ms"] / result["processed"]
            logger.info(f"[SPEED] Processed {result['processed']} events, avg {int(avg_time)}ms each")
        
        return result


# =============================================================================
# GPT REWRITE SYSTEM - QUALITÄTS-ENGINE
# =============================================================================

# Verbotene AI-Phrasen
FORBIDDEN_PHRASES = [
    "es bleibt abzuwarten",
    "es wird spannend",
    "die zeit wird zeigen",
    "nur die zukunft wird zeigen",
    "es ist noch unklar",
    "es könnte sein",
    "möglicherweise",
    "eventuell",
    "unter umständen",
    "in den kommenden wochen",
    "in naher zukunft",
    "es ist nicht auszuschließen",
    "es ist anzunehmen",
    "man darf gespannt sein",
    "es zeichnet sich ab",
    "bemerkenswert",
    "interessanterweise",
    "überraschenderweise",
    "werden zeigen",
    "sind gespannt",
    "bleibt spannend",
    "wird sich zeigen",
    "abzuwarten bleibt",
    "beobachter sind gespannt",
    "die kommenden wochen",
]


class GPTRewriter:
    """
    Qualitäts-Rewrite-Engine für Transfer-Artikel.
    
    REGELN:
    - Mindestens 120 Wörter, Ziel 120-220
    - Strukturierte Absätze (Fakten → Kontext → Einordnung)
    - Keine Kürzungen
    - Keine AI-Floskeln
    - Max 20 Wörter pro Satz
    - Fallback auf Original wenn Rewrite schlechter
    """
    
    MIN_WORDS = 150
    MAX_WORDS = 300
    MAX_SENTENCE_WORDS = 25
    
    SYSTEM_PROMPT = """Du bist Sportredakteur bei transfernews.de.

AUFGABE: Schreibe einen ausführlichen, SEO-optimierten Transfer-Artikel mit H2-Überschriften.

STRUKTUR (PFLICHT):
1. Einleitungs-Absatz (2-3 Sätze, keine Überschrift)
2. ## Die Fakten
   - Was ist passiert? Wer wechselt wohin?
3. ## Hintergrund
   - Spieler-Info, Karriere, Kontext
4. ## Bedeutung für [Vereinsname]
   - Was bedeutet der Transfer?
5. ## Ausblick
   - Nächste Schritte, was passiert als nächstes?

H2-REGELN:
- Jede H2 mit ## beginnen
- Kurz und prägnant (max 5 Wörter)
- Vereins- oder Spielernamen einbauen wenn passend
- KEINE generischen H2s wie "Einleitung" oder "Fazit"

LÄNGE: 180-280 Wörter. Je mehr Kontext, desto länger!

SATZ-REGELN:
- Max 25 Wörter pro Satz
- Aktive Sprache
- Keine Füllwörter

VERBOTEN:
- "Es bleibt abzuwarten"
- "Möglicherweise"
- "Die kommenden Wochen werden zeigen"
- Erfundene Statistiken

NUR OUTPUT: Der Artikel-Text mit H2-Überschriften."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    def validate_rewrite(self, original: str, rewrite: str, allow_context_numbers: bool = False) -> tuple[bool, str]:
        """
        Validiert den Rewrite gegen Qualitätsregeln.
        
        Returns:
            (is_valid, rejection_reason)
        """
        import re
        
        original_words = len(original.split())
        rewrite_words = len(rewrite.split())
        
        # Regel 1: Mindestlänge
        if rewrite_words < self.MIN_WORDS:
            return (False, f"Zu kurz: {rewrite_words} < {self.MIN_WORDS} Wörter")
        
        # Regel 2: Nicht kürzer als Original (mit 5% Toleranz)
        min_required = int(original_words * 0.95)
        if rewrite_words < min_required:
            return (False, f"Kürzer als Original: {rewrite_words} vs {original_words}")
        
        # Regel 3: Keine verbotenen Phrasen
        rewrite_lower = rewrite.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in rewrite_lower:
                return (False, f"Verbotene Phrase: '{phrase}'")
        
        # Regel 4: Satzlänge prüfen
        sentences = [s.strip() for s in rewrite.replace('\n', ' ').split('.') if s.strip()]
        long_sentences = [s for s in sentences if len(s.split()) > self.MAX_SENTENCE_WORDS]
        if len(long_sentences) > 2:
            return (False, f"Zu viele lange Sätze (>{self.MAX_SENTENCE_WORDS} Wörter): {len(long_sentences)}")
        
        # Regel 5: Mindestens 5 Sätze
        if len(sentences) < 5:
            return (False, f"Zu wenig Sätze: {len(sentences)} < 5")
        
        # Regel 6: H2-Überschriften erforderlich (mindestens 2)
        h2_count = len(re.findall(r'^##\s+\w', rewrite, re.MULTILINE))
        if h2_count < 2:
            return (False, f"Zu wenig H2-Überschriften: {h2_count} < 2")
        
        # Regel 7: Prüfe auf erfundene Statistiken (nur wenn kein Kontext)
        if not allow_context_numbers:
            original_numbers = set(re.findall(r'\b\d+\b', original))
            rewrite_numbers = set(re.findall(r'\b\d+\b', rewrite))
            new_numbers = rewrite_numbers - original_numbers
            suspicious_numbers = [n for n in new_numbers if 10 < int(n) < 2020]
            if len(suspicious_numbers) > 3:
                return (False, f"Verdacht auf erfundene Statistiken: {suspicious_numbers}")
        
        return (True, "OK")
    
    def clean_rewrite(self, text: str) -> str:
        """Bereinigt den Rewrite-Output (behält H2-Überschriften)"""
        import re
        # Entferne mehrfache Leerzeilen
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Entferne **fett** und *kursiv* Markdown
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        # Normalisiere H2 (## Titel statt ##Titel)
        text = re.sub(r'^##(\S)', r'## \1', text, flags=re.MULTILINE)
        return text.strip()
    
    async def rewrite_article(self, article_id: str) -> bool:
        """
        Verbessert einen Artikel mit GPT + Online-Kontext-Recherche.
        """
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            from context_research import get_context_researcher
            
            api_key = os.environ.get("EMERGENT_LLM_KEY")
            if not api_key:
                logger.warning("[GPT] No EMERGENT_LLM_KEY found, skipping rewrite")
                return False
            
            # Artikel laden
            article = await self.db.articles.find_one(
                {"id": article_id, "needs_gpt_rewrite": True},
                {"_id": 0}
            )
            
            if not article:
                return False
            
            original_body = article.get('body', '')
            original_words = len(original_body.split())
            title = article.get('title', '')
            player = article.get('player_name', '')
            club = article.get('club_name', '')
            from_club = article.get('from_club', '')
            
            # === KONTEXT-RECHERCHE ===
            researcher = get_context_researcher()
            context_data = await researcher.research_transfer(
                player_name=player,
                from_club=from_club,
                to_club=club
            )
            
            context_text = context_data.get("context_text", "")
            has_context = context_data.get("has_context", False)
            
            if has_context:
                logger.info(f"[GPT] Found online context for {player}/{club}")
            
            # GPT-Rewrite mit Kontext
            chat = LlmChat(
                api_key=api_key,
                session_id=f"rewrite-{article_id}",
                system_message=self.SYSTEM_PROMPT
            ).with_model("openai", "gpt-4o")
            
            # Prompt mit Kontext
            min_words = max(self.MIN_WORDS, original_words)
            if has_context:
                min_words = max(180, original_words)  # Mit Kontext längere Artikel
            
            prompt = f"""ARTIKEL ZUM VERBESSERN:

TITEL: {title}
SPIELER: {player}
VEREIN: {club}

ORIGINAL-TEXT:
{original_body}

"""
            if context_text:
                prompt += f"""=== RECHERCHIERTE FAKTEN (NUTZE DIESE!) ===
{context_text}
============================================

"""
            
            prompt += f"""ANFORDERUNG: Schreibe einen Artikel mit mindestens {min_words} Wörtern.
Nutze alle verfügbaren Fakten aus dem Original UND dem Kontext.
Liefere NUR den Artikel-Text."""
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            if not response:
                logger.warning(f"[GPT] Empty response for {title[:30]}")
                return False
            
            # Bereinigen
            rewrite = self.clean_rewrite(response)
            
            # Validieren (mit Kontext erlauben wir Zahlen aus Wikipedia)
            is_valid, reason = self.validate_rewrite(original_body, rewrite, allow_context_numbers=has_context)
            
            if not is_valid:
                logger.warning(f"[GPT] REJECTED: {reason} - {title[:30]}")
                
                # Retry
                retry_prompt = f"""DEIN OUTPUT WURDE ABGELEHNT: {reason}

ORIGINAL:
{original_body}

{f"KONTEXT:{chr(10)}{context_text}" if context_text else ""}

ANFORDERUNGEN:
- Mindestens {min_words} Wörter
- 5 Absätze
- Max 25 Wörter pro Satz
- Keine verbotenen Phrasen

Schreibe jetzt korrekt!"""
                
                user_message = UserMessage(text=retry_prompt)
                response = await chat.send_message(user_message)
                
                if response:
                    rewrite = self.clean_rewrite(response)
                    is_valid, reason = self.validate_rewrite(original_body, rewrite, allow_context_numbers=has_context)
                
                if not is_valid:
                    logger.error(f"[GPT] FINAL REJECT: {reason}")
                    await self.db.articles.update_one(
                        {"id": article_id},
                        {"$set": {"needs_gpt_rewrite": False, "rewrite_failed": True}}
                    )
                    return False
            
            # Erfolg: Speichern
            new_words = len(rewrite.split())
            await self.db.articles.update_one(
                {"id": article_id},
                {
                    "$set": {
                        "body": rewrite,
                        "needs_gpt_rewrite": False,
                        "gpt_rewritten_at": datetime.now(timezone.utc).isoformat(),
                        "word_count": new_words,
                        "reading_time_minutes": max(1, new_words // 200),
                        "rewrite_validation": "passed",
                        "has_researched_context": has_context,
                    }
                }
            )
            logger.info(f"[GPT] ✓ {title[:30]}... ({original_words} → {new_words} Wörter, context={has_context})")
            return True
        
        except Exception as e:
            logger.error(f"[GPT] Rewrite error: {e}")
        
        return False
    
    async def generate_meta_description(self, article: dict) -> str:
        """
        Generiert Meta-Description nach Regeln:
        - 1-2 Sätze
        - Nur Fakten
        - Keine Werbung/Clickbait
        """
        title = article.get('title', '')
        player = article.get('player_name', 'Spieler')
        club = article.get('club_name', 'Verein')
        status = article.get('transfer_status', 'GERÜCHT')
        
        if status == "OFFIZIELL":
            return f"{player} wechselt zu {club}. Der Transfer wurde offiziell bestätigt."
        elif status == "BESTÄTIGT":
            return f"{player} und {club} haben sich geeinigt. Offizielle Bestätigung steht aus."
        elif status == "FORTGESCHRITTEN":
            return f"{player} verhandelt mit {club}. Einigung in Sicht."
        else:
            return f"{player} wird mit {club} in Verbindung gebracht. Details zum möglichen Transfer."
    
    async def process_rewrite_queue(self, limit: int = 5) -> dict:
        """Verarbeitet ausstehende Rewrites"""
        result = {"rewritten": 0, "errors": 0, "rejected": 0}
        
        # Artikel die Rewrite brauchen
        articles = await self.db.articles.find(
            {"needs_gpt_rewrite": True}
        ).sort("published_at", 1).limit(limit).to_list(limit)
        
        for article in articles:
            success = await self.rewrite_article(article.get("id"))
            if success:
                result["rewritten"] += 1
            else:
                # Prüfen ob rejected oder error
                updated = await self.db.articles.find_one({"id": article.get("id")})
                if updated and updated.get("rewrite_failed"):
                    result["rejected"] += 1
                else:
                    result["errors"] += 1
        
        return result


# =============================================================================
# INTERNAL LINKS UPDATER
# =============================================================================

class InternalLinksUpdater:
    """
    Aktualisiert interne Verlinkungen nach Artikel-Erstellung.
    Fördert schnelleres Google-Crawling.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def update_links_for_article(self, article: dict):
        """
        Aktualisiert Verlinkungen:
        - Spieler-Seite
        - Club-Seite
        - Startseite (implizit durch neue Artikel)
        """
        player = article.get("player_name", "")
        club = article.get("club_name", "")
        article_id = article.get("id")
        
        # Player-Link in DB speichern (für Spieler-Seite)
        if player and player != "Unbekannter Spieler":
            await self.db.article_links.update_one(
                {"entity_type": "player", "entity_name": player},
                {
                    "$addToSet": {"article_ids": article_id},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                },
                upsert=True
            )
        
        # Club-Link in DB speichern (für Club-Seite)
        if club and club != "Unbekannter Verein":
            await self.db.article_links.update_one(
                {"entity_type": "club", "entity_name": club},
                {
                    "$addToSet": {"article_ids": article_id},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                },
                upsert=True
            )
        
        logger.debug(f"[LINKS] Updated for {player} / {club}")


# =============================================================================
# EXPORT
# =============================================================================

async def create_speed_pipeline(db: AsyncIOMotorDatabase) -> SpeedPipeline:
    """Factory für Speed Pipeline"""
    return SpeedPipeline(db)

async def create_gpt_rewriter(db: AsyncIOMotorDatabase) -> GPTRewriter:
    """Factory für GPT Rewriter"""
    return GPTRewriter(db)

async def create_links_updater(db: AsyncIOMotorDatabase) -> InternalLinksUpdater:
    """Factory für Links Updater"""
    return InternalLinksUpdater(db)
