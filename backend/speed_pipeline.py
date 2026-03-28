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
    
    # Body Templates (kurz, faktisch, kein AI-Smell)
    BODY_TEMPLATES = {
        "official": """## Transfer bestätigt

{source_name} berichtet: {headline}

{player} wird künftig für {club} auflaufen. Der Wechsel wurde offiziell verkündet.

## Quelle

Laut {source_name} ist der Deal perfekt. Weitere Details werden erwartet.

*Zuletzt aktualisiert: {timestamp}*""",

        "confirmed": """## Einigung erzielt

{source_name} meldet: {headline}

{player} und {club} haben sich geeinigt. Der Transfer steht kurz vor dem Abschluss.

## Hintergrund

Die Verhandlungen sind abgeschlossen. Eine offizielle Bestätigung wird in Kürze erwartet.

*Zuletzt aktualisiert: {timestamp}*""",

        "advanced": """## Verhandlungen laufen

{source_name} berichtet: {headline}

{player} befindet sich in Gesprächen mit {club}. Ein Wechsel ist möglich.

## Aktuelle Lage

Die Verhandlungen sind fortgeschritten. Eine Entscheidung könnte bald fallen.

*Zuletzt aktualisiert: {timestamp}*""",

        "rumour": """## Transfer-Gerücht

{source_name} meldet: {headline}

{player} wird mit einem Wechsel zu {club} in Verbindung gebracht.

## Einschätzung

Es handelt sich um ein Gerücht. Konkrete Verhandlungen sind nicht bestätigt.

*Zuletzt aktualisiert: {timestamp}*"""
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
    
    def extract_entities(self, headline: str, body: str = "") -> Dict[str, str]:
        """Extrahiert Spieler und Club aus Text"""
        text = f"{headline} {body}".lower()
        
        # Known players (erweitert)
        KNOWN_PLAYERS = {
            "mbappe": "Kylian Mbappé", "haaland": "Erling Haaland",
            "bellingham": "Jude Bellingham", "messi": "Lionel Messi",
            "ronaldo": "Cristiano Ronaldo", "salah": "Mohamed Salah",
            "kane": "Harry Kane", "musiala": "Jamal Musiala",
            "wirtz": "Florian Wirtz", "saka": "Bukayo Saka",
            "palmer": "Cole Palmer", "vinicius": "Vinícius Jr.",
            "pedri": "Pedri", "gavi": "Gavi", "yamal": "Lamine Yamal",
            "sancho": "Jadon Sancho", "rashford": "Marcus Rashford",
            "trafford": "James Trafford", "vicario": "Guglielmo Vicario",
        }
        
        # Known clubs
        KNOWN_CLUBS = {
            "real madrid": "Real Madrid", "barcelona": "FC Barcelona",
            "bayern": "FC Bayern München", "dortmund": "Borussia Dortmund",
            "manchester city": "Manchester City", "man city": "Manchester City",
            "liverpool": "FC Liverpool", "chelsea": "FC Chelsea",
            "arsenal": "FC Arsenal", "manchester united": "Manchester United",
            "man united": "Manchester United", "tottenham": "Tottenham Hotspur",
            "psg": "Paris Saint-Germain", "juventus": "Juventus Turin",
            "inter": "Inter Mailand", "milan": "AC Milan",
            "napoli": "SSC Neapel", "roma": "AS Rom",
            "atletico": "Atlético Madrid", "sevilla": "FC Sevilla",
            "newcastle": "Newcastle United", "west ham": "West Ham United",
            "everton": "FC Everton", "leicester": "Leicester City",
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
        
        return {"player": player, "club": club}
    
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
# GPT REWRITE SYSTEM (Async, Hintergrund)
# =============================================================================

class GPTRewriter:
    """
    Verbessert Instant-Artikel asynchron mit GPT.
    Läuft im Hintergrund, blockiert nicht die Veröffentlichung.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def rewrite_article(self, article_id: str) -> bool:
        """
        Verbessert einen Artikel mit GPT.
        NUR Umformulierung, KEINE neuen Fakten!
        """
        try:
            from emergentintegrations.llm.chat import LlmChat
            
            api_key = os.environ.get("LLM_API_KEY")
            if not api_key:
                logger.warning("[GPT] No API key, skipping rewrite")
                return False
            
            # Artikel laden
            article = await self.db.articles.find_one(
                {"id": article_id, "needs_gpt_rewrite": True},
                {"_id": 0}
            )
            
            if not article:
                return False
            
            # GPT-Rewrite
            chat = LlmChat(
                api_key=api_key,
                session_id=f"rewrite-{article_id}",
                system_message="""Du bist Redakteur bei transfernews.de.
                
AUFGABE: Verbessere den folgenden Artikel sprachlich.

REGELN:
1. KEINE neuen Fakten hinzufügen
2. NUR vorhandene Informationen umformulieren
3. Deutscher Journalismus-Stil
4. Kurze, klare Sätze
5. Absätze mit ## Zwischenüberschriften
6. Max 300 Wörter

OUTPUT: Nur der verbesserte Artikel-Body, kein JSON."""
            )
            
            prompt = f"""Verbessere diesen Artikel:

TITEL: {article.get('title', '')}

AKTUELLER TEXT:
{article.get('body', '')}

Liefere NUR den verbesserten Text."""
            
            response = await chat.send_async(prompt)
            
            if response and len(response) > 100:
                await self.db.articles.update_one(
                    {"id": article_id},
                    {
                        "$set": {
                            "body": response,
                            "needs_gpt_rewrite": False,
                            "gpt_rewritten_at": datetime.now(timezone.utc).isoformat(),
                            "word_count": len(response.split()),
                            "reading_time_minutes": max(1, len(response.split()) // 200),
                        }
                    }
                )
                logger.info(f"[GPT] Article rewritten: {article.get('title', '')[:40]}")
                return True
        
        except Exception as e:
            logger.error(f"[GPT] Rewrite error: {e}")
        
        return False
    
    async def process_rewrite_queue(self, limit: int = 5) -> dict:
        """Verarbeitet ausstehende Rewrites"""
        result = {"rewritten": 0, "errors": 0}
        
        # Artikel die Rewrite brauchen
        articles = await self.db.articles.find(
            {"needs_gpt_rewrite": True}
        ).sort("published_at", 1).limit(limit).to_list(limit)
        
        for article in articles:
            success = await self.rewrite_article(article.get("id"))
            if success:
                result["rewritten"] += 1
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
