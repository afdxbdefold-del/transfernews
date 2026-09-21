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
from uuid import uuid4, uuid5, NAMESPACE_URL
from pymongo import ReturnDocument
from pipeline_state import utcnow, parse_source_time, review_reason, retry_at, due_query, story_lease
from transfer_evidence import assess_transfer_evidence, unsupported_headline_detail
from entity_catalogue import load_entity_catalogues
from publication_policy import PIPELINE_VERSION, RECONSIDER_REASONS, editorial_eligibility, can_publish_rewrite
from source_rewrite_checks import validate_source_rewrite

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
    
    FLOW (NEU mit Story Engine):
    1. RSS Event kommt rein
    2. Story Engine: Entity Extraction + Story Match
    3. Story Engine: Source Weighting + Stage Detection
    4. Story Engine Decision: create_article / update_article / merge_only / skip
    5. Bei create/update: Instant-Artikel generieren
    6. Async: GPT-Rewrite queuen
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.instant_generator = InstantArticleGenerator()
        self.dedupe = DedupeSystem()
        self.evidence_catalogues = None
        
        # Story Engine für Duplicate Killer
        from story_engine import get_story_engine
        self.story_engine = get_story_engine(db)
    
    async def process_event(self, event: dict) -> dict:
        start = utcnow()
        reason = review_reason(event)
        if reason:
            return {"action": "review", "reason": reason, "article_id": None, "time_ms": 0}
        event = dict(event)
        event["title"] = event.get("headline_raw") or event.get("title", "")
        event["headline_raw"] = event["title"]
        event["summary"] = event.get("summary") or event.get("body_raw") or event.get("summary_raw", "")
        if self.evidence_catalogues is None:
            self.evidence_catalogues = await load_entity_catalogues(self.db)
        entities = assess_transfer_evidence(event["title"], event["summary"], self.evidence_catalogues)
        if entities.get("reason"):
            return {"action": "review", "reason": entities["reason"], "article_id": None, "time_ms": 0}
        event["evidence_scope"] = entities["evidence_scope"]
        if event["evidence_scope"] == "headline":
            # Local copy only: preserve the original imported event for editorial review.
            # Clear every summary alias so StoryEngine cannot fall back to mixed RSS text.
            event.update(summary="", body_raw="", summary_raw="")
        player, club = entities.get("player", ""), entities.get("club", "")
        if (not player or not club or any("unbekannt" in value.lower() or "unknown" in value.lower()
                                        for value in (player, club))):
            return {"action": "review", "reason": "unresolved_entities", "article_id": None, "time_ms": 0}
        event.update(player_name=player, club_name=club, from_club=entities.get("from_club"),
                     entity_confidence=entities.get("confidence", 0.5))
        event["verified_transfer_type"] = entities.get("transfer_type")
        transfer_type = (event["verified_transfer_type"] or
                         self.story_engine.extract_entities(event["title"], event["summary"], event.get("source_name", ""))["transfer_type"])
        identity = self.story_engine.generate_story_key(self.story_engine._slugify(player), self.story_engine._slugify(club), transfer_type)
        async with story_lease(self.db, identity):
            result = await self.story_engine.process_incoming_event(event)
            story = result.get("story")
            if not story:
                return {"action": "review", "reason": result.get("reason", "missing_story"), "article_id": None, "time_ms": 0}
            article_id = story.get("article_id")
            article = await self.db.articles.find_one({"id": article_id}) if article_id else None
            if article is None:
                article = await self._create_article_from_story(result, event, is_draft=True)
                if not article:
                    raise RuntimeError("article_creation_failed")
                action = "created" if article.get("status") == "published" else "created_draft"
            elif (result.get("action") == "skip" and
                  article.get("story_revision", -1) == story.get("update_count", 0) and
                  article.get("publication_policy_version") == PIPELINE_VERSION):
                action = "skipped"
            else:
                await self._update_article_from_story(article["id"], result, event)
                action = "updated"
            await self.db.transfer_stories.update_one({"_id": story["_id"]}, {"$set": {"article_id": article["id"]}})
        return {"action": action, "article_id": article["id"], "story_key": story["story_key"],
                "reason": result.get("reason"), "time_ms": int((utcnow() - start).total_seconds() * 1000)}

    @staticmethod
    def _source_article_body(story: dict, event: dict) -> str:
        """Publish supplied facts, without the old invented negotiations/background templates."""
        if event.get("evidence_scope") == "headline":
            return "## Quellenmeldung\n\n" + (event.get("source_name") or "Die Quelle") + ": " + event["title"]
        pieces = ["## Transferstand", story["headline"] + "."]
        if story.get("transfer_fee"):
            pieces.append("Gemeldete Ablöse: " + story["transfer_fee"] + ".")
        pieces.extend(["## Quellenmeldung", (event.get("source_name") or "Die Quelle") + ": " + event["title"]])
        if event.get("summary"):
            pieces.append(event["summary"])
        return "\n\n".join(pieces)
    
    async def _create_article_from_story(self, story_result: dict, event: dict, is_draft: bool = False) -> dict:
        story = story_result["story"]
        article_id = story.get("article_id") or str(uuid5(NAMESPACE_URL, "transfernews:" + str(story["_id"])))
        existing = await self.db.articles.find_one({"id": article_id})
        if existing:
            return existing
        article = self.instant_generator.generate_instant_article(event)
        now = utcnow().isoformat()
        eligible, publication_reason = editorial_eligibility(event, story)
        article.update({
            "_id": "article:" + article_id, "id": article_id,
            "title": story["headline"], "slug": story["slug"],
            "status": "draft", "is_draft": True,
            "published_at": None, "created_at": now, "updated_at": now,
            "transfer_status": story["current_stage"], "confidence_score": story["confidence_score"],
            "transfer_probability": story["confidence_score"],
            "story_key": story["story_key"], "story_id": str(story["_id"]),
            "dedupe_key": story["story_key"], "primary_source": story.get("primary_source", ""),
            "secondary_sources": story.get("secondary_sources", []), "transfer_fee": story.get("transfer_fee", ""),
            "story_region": story.get("story_region", "global"),
            "source_event_id": event.get("id"), "source_published_at": parse_source_time(event.get("source_published_at")),
            "source_headline": event["title"], "source_summary": event.get("summary", ""),
            "evidence_scope": event.get("evidence_scope", "full"),
            "source_grounded": True, "transfer_type": story.get("transfer_type", "permanent"),
            "source_name": event.get("source_name", ""), "source_url": event.get("source_url", ""),
            "auto_publish_eligible": eligible, "publication_reason": publication_reason,
            "publication_policy_version": PIPELINE_VERSION,
            "player_name": story["player_name"], "club_name": story["target_club"],
            "from_club": event.get("from_club"), "entity_confidence": event["entity_confidence"],
            "author_name": "Redaktion", "author_slug": "redaktion",
            "needs_gpt_rewrite": eligible, "rewrite_status": "pending" if eligible else "review", "rewrite_attempts": 0,
            "content_revision": 1, "story_revision": story.get("update_count", 0),
        })
        # Keep the lead consistent with the story decision instead of a second status classifier.
        article["excerpt"] = story["headline"]
        article["body"] = self._source_article_body(story, event)
        article["word_count"] = len(article["body"].split())
        await self._assign_article_image(article)
        await self.db.articles.update_one({"_id": article["_id"]}, {"$setOnInsert": article}, upsert=True)
        saved = await self.db.articles.find_one({"_id": article["_id"]}, {"_id": 0})
        return saved
    
    async def _update_article_from_story(self, article_id: str, story_result: dict, event: dict):
        story = story_result["story"]
        article = await self.db.articles.find_one({"id": article_id})
        if article is None:
            raise RuntimeError("article_missing")
        now = utcnow().isoformat()
        eligible, publication_reason = editorial_eligibility(event, story)
        fields = {
            "updated_at": now, "title": story["headline"], "excerpt": story["headline"],
            "transfer_status": story["current_stage"], "confidence_score": story["confidence_score"],
            "transfer_probability": story["confidence_score"], "transfer_fee": story.get("transfer_fee", ""),
            "primary_source": story.get("primary_source", ""), "secondary_sources": story.get("secondary_sources", []),
            "source_headline": event["title"], "source_summary": event.get("summary", ""),
            "evidence_scope": event.get("evidence_scope", "full"),
            "source_grounded": True, "transfer_type": story.get("transfer_type", "permanent"),
            "auto_publish_eligible": eligible, "publication_reason": publication_reason,
            "publication_policy_version": PIPELINE_VERSION,
            "source_published_at": parse_source_time(event.get("source_published_at")),
            "source_url": event.get("source_url", ""),
            "source_name": event.get("source_name", ""),
            "player_name": story["player_name"], "club_name": story["target_club"],
            "from_club": event.get("from_club"), "entity_confidence": event.get("entity_confidence", 0.5),
            "needs_gpt_rewrite": eligible, "rewrite_status": "pending" if eligible else "review", "rewrite_attempts": 0,
            "rewrite_failed": False,
            "story_revision": story.get("update_count", 0),
        }
        # Keep the currently published text and headline until the new revision passes review.
        fields["source_template"] = self._source_article_body(story, event)
        if article.get("status") == "published":
            public_keys = ("title", "excerpt", "transfer_status", "confidence_score", "transfer_probability",
                           "transfer_fee", "primary_source", "secondary_sources", "transfer_type")
            fields["pending_publication"] = {key: fields.pop(key) for key in public_keys}
        else:
            fields["body"] = fields["source_template"]
            fields["word_count"] = len(fields["body"].split())
        await self.db.articles.update_one({"_id": article["_id"]}, {
            "$set": fields, "$inc": {"content_revision": 1},
            "$unset": {"rewrite_next_attempt_at": "", "rewrite_lease_until": "", "rewrite_token": "",
                       "rewrite_validation": "", "rewrite_completed_revision": "", "is_gpt_rewritten": "",
                       "gpt_rewritten_at": ""},
        })
    
    async def _assign_article_image(self, article_data: dict):
        """Weist einem Artikel ein Bild zu"""
        try:
            from wikimedia_images import get_article_image_service
            
            image_service = get_article_image_service(self.db)
            player = article_data.get("player_name", "")
            
            # Artikel-Daten für Bildsuche vorbereiten
            article_for_image = {
                "title": article_data.get("title", ""),
                "body": article_data.get("body", ""),
            }
            
            # Wikimedia-Bild suchen
            image_result = await image_service.process_article(article_for_image)
            
            if image_result and image_result.url:
                article_data["hero_image"] = image_result.url
                article_data["hero_image_meta"] = {
                    "author": image_result.author,
                    "license": image_result.license_name,
                    "source_url": image_result.source_url,
                    "score": image_result.quality_score
                }
                article_data["hero_image_source"] = "wikimedia"
        except Exception as e:
            logger.warning(f"[PIPELINE] Image assignment failed: {e}")
    
    # === LEGACY METHODS (für Kompatibilität) ===
    
    async def process_event_legacy(self, event: dict) -> dict:
        """Compatibility entry point, with the same freshness and identity protections."""
        return await self.process_event(event)
    
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
        result = {"processed": 0, "created": 0, "created_draft": 0, "updated": 0,
                  "skipped": 0, "review": 0, "retry": 0, "total_time_ms": 0, "errors": []}
        for _ in range(limit):
            now, token = utcnow(), uuid4().hex
            ready = {"$or": [
                {"$and": [{"status": {"$in": ["pending", "retry"]}}, due_query("next_attempt_at", now)]},
                {"status": "processing", "lease_until": {"$lte": now}},
                {"pipeline_version": {"$ne": PIPELINE_VERSION},
                 "source_published_at": {"$gte": now - timedelta(hours=48), "$lte": now + timedelta(minutes=10)},
                 "$or": [{"status": "review", "review_reason": {"$in": list(RECONSIDER_REASONS)}},
                         {"status": "processed", "processing_outcome": {"$in": ["created_draft", "updated"]}}]},
            ]}
            # Evaluate the old state atomically: a deliberate new-policy review
            # starts a new budget; ordinary retries / expired leases retain it.
            policy_reconsideration = {"$and": [
                {"$in": ["$status", ["review", "processed"]]},
                {"$ne": [{"$ifNull": ["$pipeline_version", None]}, PIPELINE_VERSION]},
            ]}
            event = await self.db.events.find_one_and_update(ready, [{"$set": {
                "status": "processing", "lease_token": token, "lease_until": now + timedelta(minutes=5),
                "processing_attempts": {"$cond": [policy_reconsideration, 1,
                    {"$add": [{"$ifNull": ["$processing_attempts", 0]}, 1]}]},
            }}], sort=[("created_at", 1), ("_id", 1)], return_document=ReturnDocument.AFTER)
            if event is None:
                break
            selector = {"_id": event["_id"], "lease_token": token}
            try:
                if event["processing_attempts"] > 5:
                    raise RuntimeError("attempt_limit")
                outcome = await asyncio.wait_for(self.process_event(event), timeout=180)
                action = outcome["action"]
                status = "review" if action == "review" else "processed"
                fields = {"status": status, "processed_at": utcnow(), "processing_outcome": action,
                          "pipeline_version": PIPELINE_VERSION,
                          "review_reason": outcome.get("reason") if status == "review" else None,
                          "article_id": outcome.get("article_id"), "story_key": outcome.get("story_key")}
                completed = await self.db.events.update_one(selector, {"$set": fields, "$unset": {
                    "lease_token": "", "lease_until": "", "next_attempt_at": "", "error": ""}})
                if completed.matched_count:
                    result["processed"] += 1
                    result[action] = result.get(action, 0) + 1
                    result["total_time_ms"] += outcome.get("time_ms", 0)
            except Exception as exc:
                attempt = event.get("processing_attempts", 1)
                terminal = attempt >= 5
                error_code = type(exc).__name__
                fields = {"status": "error" if terminal else "retry", "error": error_code,
                          "next_attempt_at": retry_at(attempt), "last_attempt_at": utcnow()}
                await self.db.events.update_one(selector, {"$set": fields, "$unset": {"lease_token": "", "lease_until": ""}})
                result["errors"].append(error_code)
                if not terminal:
                    result["retry"] += 1
        logger.info("[SPEED] completed=%s created=%s drafts=%s updated=%s review=%s retry=%s errors=%s",
                    result["processed"], result["created"], result["created_draft"], result["updated"],
                    result["review"], result["retry"], len(result["errors"]))
        return result


# =============================================================================
# GPT REWRITE SYSTEM - QUALITÄTS-ENGINE
# =============================================================================

# Verbotene AI-Phrasen
FORBIDDEN_PHRASES = [
    # Nur wirklich schlechte AI-Floskeln
    "es bleibt abzuwarten",
    "die zeit wird zeigen",
    "nur die zukunft wird zeigen",
    "man darf gespannt sein",
    "es zeichnet sich ab",
    "beobachter sind gespannt",
    "es ist nicht auszuschließen",
    "abzuwarten bleibt",
    # Zu vage
    "es könnte sein dass",
    "unter umständen könnte",
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

    HEADLINE_SYSTEM_PROMPT = """Du bist Sportredakteur bei transfernews.de.
Schreibe eine kurze deutsche Meldung ausschließlich aus der angegebenen Quellenüberschrift.
Bewahre deren Unsicherheit und nenne die Quelle. Keine Vermutungen, zusätzlichen Details,
Karrierefakten, Motive, Statistiken oder Angaben aus Vorwissen ergänzen.
Insbesondere keine Nationalität, kein Alter, keine Spielposition, keinen Herkunftsverein
und keine biografischen Angaben nennen, sofern diese nicht in der Quellenüberschrift stehen.
15 bis 80 Wörter, zwei bis vier kurze Sätze, eine H2-Überschrift mit ##.
Vermeide Fülltext; liefere nur die Meldung."""

    SOURCE_SYSTEM_PROMPT = """Du bist Sportredakteur bei transfernews.de.
Schreibe eine kurze deutsche Nachricht ausschließlich aus der Quellenüberschrift und
der Quellenzusammenfassung. Nenne den angegebenen Verlag ausdrücklich als Quelle.
Bewahre Unsicherheit: Interesse, Gerücht oder bevorstehender Abschluss sind kein
vollzogener Wechsel. Eine Vertragsverlängerung ist kein Wechsel zu einem neuen Verein.
Eine Leihe ist kein dauerhafter Kauf. Erfinde keine Ablöse, Bestätigung, Zitate oder Hintergründe.
Verwende keine eigenen Kenntnisse und keine biografischen Ergänzungen. Konzentriere dich
auf die belegte Vertrags-/Transfermeldung, nicht auf beiläufige Karriereangaben.
Schreibe 25 bis 180 Wörter, mindestens zwei kurze Sätze und eine H2 mit ##.
Die Länge richtet sich nach dem Quellenmaterial. Liefere nur den Nachrichtentext."""
    
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

LÄNGE: So knapp wie die belegten Fakten es erlauben. Fehlende Fakten niemals durch Fülltext ersetzen.

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
        self.evidence_catalogues = None
    
    def validate_rewrite(self, original: str, rewrite: str, allow_context_numbers: bool = False,
                         evidence: str = "", evidence_scope: str = "full", catalogues=None) -> tuple[bool, str]:
        """
        Validiert den Rewrite gegen Qualitätsregeln.
        
        Returns:
            (is_valid, rejection_reason)
        """
        import re
        
        original_words = len(original.split())
        rewrite_words = len(rewrite.split())
        
        # Regel 1: Mindestlänge
        headline_only = evidence_scope == "headline"
        source_only = evidence_scope == "source"
        minimum = 15 if headline_only else (25 if source_only else min(self.MIN_WORDS, max(40, original_words)))
        if rewrite_words < minimum:
            return (False, f"Zu kurz: {rewrite_words} < {minimum} Wörter")
        if headline_only and rewrite_words > 80:
            return (False, "Quellenüberschrift erlaubt höchstens 80 Wörter")
        if headline_only or source_only:
            detail_error = unsupported_headline_detail(rewrite, evidence or original, catalogues)
            if detail_error:
                return (False, detail_error)
        
        # Regel 2: Nicht kürzer als Original (nur bei langen Originalen >100 Wörter)
        if not headline_only and not source_only and original_words > 100:
            min_required = int(original_words * 0.85)  # 15% Toleranz
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
        minimum_sentences = 2 if headline_only or source_only else 5
        if len(sentences) < minimum_sentences:
            return (False, f"Zu wenig Sätze: {len(sentences)} < {minimum_sentences}")
        
        # Regel 6: H2-Überschriften erforderlich (mindestens 2)
        h2_count = len(re.findall(r'^##\s+\w', rewrite, re.MULTILINE))
        minimum_headings = 1 if headline_only or source_only else 2
        if h2_count < minimum_headings:
            return (False, f"Zu wenig H2-Überschriften: {h2_count} < {minimum_headings}")
        
        # Regel 7: Prüfe auf erfundene Statistiken (nur wenn kein Kontext)
        if not allow_context_numbers:
            original_numbers = set(re.findall(r'\b\d+\b', original + "\n" + evidence))
            rewrite_numbers = set(re.findall(r'\b\d+\b', rewrite))
            new_numbers = rewrite_numbers - original_numbers
            suspicious_numbers = sorted(new_numbers)
            if suspicious_numbers:
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
        openai_client = None
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.warning("[GPT] No OPENAI_API_KEY found, skipping rewrite")
                return False
            
            from openai import AsyncOpenAI
            openai_client = AsyncOpenAI(api_key=api_key, timeout=60, max_retries=1)
            
            # Artikel laden
            article = await self.db.articles.find_one(
                {"id": article_id, "needs_gpt_rewrite": True},
                {"_id": 0}
            )
            
            if not article:
                return False

            source_grounded = article.get("source_grounded", False)
            if source_grounded and not article.get("auto_publish_eligible"):
                return False
            if self.evidence_catalogues is None:
                self.evidence_catalogues = await load_entity_catalogues(self.db)
            source_article = {**article, **article.get("pending_publication", {})}

            headline_only = article.get("evidence_scope") == "headline"
            source_headline = article.get("source_headline", "")
            if headline_only and not source_headline.strip():
                return False
            source_summary = "" if headline_only else article.get("source_summary", "")
            # A prior rewrite or older story is not a source for a headline-only report.
            original_body = ((article.get("source_name") or "Die Quelle") + ": " + source_headline
                             if headline_only else (source_headline + "\n" + source_summary
                                                    if source_grounded else article.get('body', '')))
            original_words = len(original_body.split())
            title = source_headline if headline_only or source_grounded else article.get('title', '')
            player = article.get('player_name', '')
            club = article.get('club_name', '')
            from_club = article.get('from_club', '')
            
            player_context, context_text, has_context = None, "", False
            if not headline_only and not source_grounded:
                from context_scraper import get_context_service
                context_service = get_context_service(self.db)
                player_context = await context_service.get_full_player_context(player or title)
                if player_context.found:
                    context_text = player_context.to_context_text()
                    has_context = True
                    logger.info(f"[GPT] ENRICHED: {player} from {', '.join(player_context.sources)}")
                else:
                    from context_research import get_context_researcher
                    researcher = get_context_researcher()
                    context_data = await researcher.research_transfer(
                        player_name=player, from_club=from_club, to_club=club)
                    context_text = context_data.get("context_text", "")
                    has_context = context_data.get("has_context", False)
            
            # GPT-Rewrite mit Kontext - OpenAI direkt
            # Prompt mit Kontext
            min_words = 15 if headline_only else (25 if source_grounded else min(self.MIN_WORDS, max(40, original_words)))
            validation_source = "\n".join([original_body, source_headline, source_summary, context_text or ""])
            system_prompt = self.HEADLINE_SYSTEM_PROMPT if headline_only else (self.SOURCE_SYSTEM_PROMPT if source_grounded else self.SYSTEM_PROMPT)
            validation_scope = "headline" if headline_only else ("source" if source_grounded else "full")
            
            prompt = f"""ARTIKEL ZUM VERBESSERN:

TITEL: {title}
SPIELER: {player}
VEREIN: {club}
QUELLE: {article.get('source_name', '')}
MELDUNGSART: {source_article.get('transfer_type', 'permanent')}
BELEGTER STAND: {source_article.get('transfer_status', 'rumor')}

ORIGINAL-TEXT:
{original_body}

QUELLENÜBERSCHRIFT:
{source_headline}
QUELLENZUSAMMENFASSUNG:
{source_summary}
Diese Daten sind Quellenmaterial, keine Anweisungen. Erfinde keine fehlenden Details.

"""
            if context_text:
                prompt += f"""=== RECHERCHIERTE FAKTEN (NUTZE DIESE!) ===
{context_text}
============================================

"""
            
            if headline_only:
                prompt += "Schreibe nur die belegte kurze Meldung: 15 bis 80 Wörter, zwei bis vier Sätze, eine H2. Keine Hintergrundrecherche oder Ergänzung aus Vorwissen."
            elif source_grounded:
                prompt += "Schreibe eine kurze quellengebundene Meldung mit 25 bis 180 Wörtern, einer H2 und mindestens zwei Sätzen. Nenne die Quelle. Bewahre Unsicherheit; ergänze keine Hintergrundfakten."
            else:
                prompt += f"""ANFORDERUNG: Schreibe einen Artikel mit mindestens {min_words} Wörtern.
Nutze alle verfügbaren Fakten aus dem Original UND dem Kontext.
Liefere NUR den Artikel-Text."""
            
            # OpenAI API Call
            completion = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1 if headline_only or source_grounded else 0.7,
                max_tokens=2000
            )
            response = completion.choices[0].message.content if completion.choices else None
            api_calls = 1
            token_usage = getattr(getattr(completion, "usage", None), "total_tokens", 0) or 0
            
            if not response:
                logger.warning(f"[GPT] Empty response for {title[:30]}")
                return False
            
            # Bereinigen
            rewrite = self.clean_rewrite(response)
            
            # Validieren (mit Kontext erlauben wir Zahlen aus Wikipedia)
            is_valid, reason = self.validate_rewrite(original_body, rewrite, evidence=validation_source,
                                                      evidence_scope=validation_scope, catalogues=self.evidence_catalogues)
            if is_valid and source_grounded:
                is_valid, reason = validate_source_rewrite(rewrite, source_article)
            
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
                if headline_only:
                    retry_prompt = f"""Der Entwurf wurde abgelehnt: {reason}
Einziger Quellenbeleg: {original_body}
Schreibe eine kurze Meldung mit 15 bis 80 Wörtern, zwei bis vier Sätzen und einer H2.
Bewahre Unsicherheit und Quellenangabe. Keine weiteren Fakten oder Hintergründe ergänzen."""
                elif source_grounded:
                    retry_prompt = f"Der Entwurf wurde abgelehnt: {reason}\nQuelle: {article.get('source_name', '')}\nMELDUNGSART: {source_article.get('transfer_type', 'permanent')}\nBELEGTER STAND: {source_article.get('transfer_status', 'rumor')}\nEinzige Fakten:\n{original_body}\nSchreibe 25 bis 180 Wörter, mindestens zwei Sätze und eine H2. Nenne die Quelle, bewahre den belegten Stand und die Meldungsart. Ergänze keine Fakten. Lass im Zweifel Alters-, Nationalitäts-, Positions- und Nationalmannschaftsangaben vollständig weg. Beschränke dich auf die belegte Vertrags- oder Transfermeldung."
                
                retry_completion = await openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": retry_prompt}
                    ],
                    temperature=0.1 if headline_only or source_grounded else 0.7,
                    max_tokens=2000
                )
                response = retry_completion.choices[0].message.content if retry_completion.choices else None
                api_calls += 1
                token_usage += getattr(getattr(retry_completion, "usage", None), "total_tokens", 0) or 0
                
                if response:
                    rewrite = self.clean_rewrite(response)
                    is_valid, reason = self.validate_rewrite(original_body, rewrite, evidence=validation_source,
                                                              evidence_scope=validation_scope, catalogues=self.evidence_catalogues)
                    if is_valid and source_grounded:
                        is_valid, reason = validate_source_rewrite(rewrite, source_article)
                
                if not is_valid:
                    logger.error(f"[GPT] FINAL REJECT: {reason}")
                    rejected_selector = {"id": article_id, "content_revision": article.get("content_revision")}
                    if article.get("rewrite_token"):
                        rejected_selector["rewrite_token"] = article["rewrite_token"]
                    await self.db.articles.update_one(
                        rejected_selector,
                        {"$set": {"needs_gpt_rewrite": False, "rewrite_failed": True, "rewrite_status": "review",
                                  "rewrite_review_reason": reason, "rewrite_api_calls": api_calls,
                                  "rewrite_tokens": token_usage,
                                  "rewrite_rejected_body": rewrite if article.get("status") == "draft" else None}}
                    )
                    return False
            
            # Erfolg: Speichern
            new_words = len(rewrite.split())
            
            # Strukturierte Spieler-Daten aus Context extrahieren
            update_fields = {
                "body": rewrite,
                "needs_gpt_rewrite": False,
                "is_gpt_rewritten": True,
                "gpt_rewritten_at": datetime.now(timezone.utc).isoformat(),
                "word_count": new_words,
                "reading_time_minutes": max(1, new_words // 200),
                "rewrite_validation": "passed",
                "rewrite_status": "complete", "rewrite_failed": False,
                "rewrite_completed_revision": article.get("content_revision"),
                "rewrite_model": "gpt-4o-mini", "rewrite_api_calls": api_calls, "rewrite_tokens": token_usage,
                "updated_at": utcnow().isoformat(),
                "has_researched_context": has_context,
            }
            if source_grounded:
                # Re-check freshness after the external call, before any public write.
                eligible, _ = editorial_eligibility(source_article, source_article)
                if not eligible:
                    return False
                allowed = {"title", "excerpt", "transfer_status", "confidence_score", "transfer_probability",
                           "transfer_fee", "primary_source", "secondary_sources", "transfer_type"}
                update_fields.update({key: value for key, value in article.get("pending_publication", {}).items() if key in allowed})
                if can_publish_rewrite(source_article):
                    update_fields.update(status="published", is_draft=False, published_at=utcnow().isoformat())
            if headline_only:
                update_fields["source_summary"] = ""
            
            # Füge strukturierte Daten hinzu wenn Kontext vorhanden
            if player_context is not None and player_context.found:
                if player_context.market_value:
                    update_fields["market_value"] = player_context.market_value
                if player_context.contract_until:
                    update_fields["contract_until"] = player_context.contract_until
                if player_context.age:
                    update_fields["player_age"] = player_context.age
                if player_context.nationality:
                    update_fields["player_nationality"] = player_context.nationality
                if player_context.position:
                    update_fields["player_position"] = player_context.position
                if player_context.full_name:
                    update_fields["player_full_name"] = player_context.full_name
                if player_context.current_club:
                    update_fields["current_club"] = player_context.current_club
            
            selector = {"id": article_id, "content_revision": article.get("content_revision"),
                        "status": article.get("status")}
            if source_grounded:
                selector.update(auto_publish_eligible=True, publication_policy_version=PIPELINE_VERSION)
                # Editorial holds can change while OpenAI is running, without
                # changing the article revision or its current public status.
                selector.update(duplicate_of={"$in": [None, ""]},
                                review_reason={"$in": [None, ""]})
            if article.get("rewrite_token"):
                selector["rewrite_token"] = article["rewrite_token"]
            updated = await self.db.articles.update_one(selector, {
                "$set": update_fields, "$unset": {"pending_publication": "", "rewrite_review_reason": "",
                                                    "rewrite_rejected_body": ""}})
            if not updated.matched_count:
                return False
            logger.info(f"[GPT] ✓ {title[:30]}... ({original_words} → {new_words} Wörter, context={has_context})")
            return True
        
        except Exception as e:
            logger.error("[GPT] Rewrite error: %s", type(e).__name__)
        finally:
            if openai_client is not None:
                await openai_client.close()
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
        result = {"rewritten": 0, "published": 0, "errors": 0, "rejected": 0}
        if not os.environ.get("OPENAI_API_KEY"):
            logger.warning("[GPT] Rewrite blocked: OPENAI_API_KEY is not configured")
            return {**result, "blocked": "missing_openai_key"}
        for _ in range(limit):
            now, token = utcnow(), uuid4().hex
            eligible = {"needs_gpt_rewrite": True, "$or": [
                {"$and": [{"rewrite_status": {"$nin": ["processing", "review", "failed"]}}, due_query("rewrite_next_attempt_at", now)]},
                {"rewrite_status": "processing", "rewrite_lease_until": {"$lte": now}},
            ]}
            article = await self.db.articles.find_one_and_update(eligible, {
                "$set": {"rewrite_status": "processing", "rewrite_token": token, "rewrite_lease_until": now + timedelta(minutes=5)},
                "$inc": {"rewrite_attempts": 1},
            }, sort=[("published_at", 1), ("_id", 1)], return_document=ReturnDocument.AFTER)
            if article is None:
                break
            selector = {"_id": article["_id"], "rewrite_token": token}
            try:
                success = False if article["rewrite_attempts"] > 5 else await asyncio.wait_for(self.rewrite_article(article["id"]), timeout=240)
            except Exception as exc:
                logger.warning("[GPT] Rewrite attempt failed: %s", type(exc).__name__)
                success = False
            current = await self.db.articles.find_one(selector)
            if current is None:
                continue  # A newer source update invalidated this lease.
            fields = {}
            if success:
                fields = {"rewrite_status": "complete", "needs_gpt_rewrite": False, "rewrite_failed": False}
                result["rewritten"] += 1
                if article.get("status") == "draft" and current.get("status") == "published":
                    result["published"] += 1
            elif current.get("rewrite_failed"):
                fields = {"rewrite_status": "review", "needs_gpt_rewrite": False}
                result["rejected"] += 1
            else:
                terminal = article["rewrite_attempts"] >= 5
                fields = {"rewrite_status": "failed" if terminal else "retry", "needs_gpt_rewrite": not terminal,
                          "rewrite_next_attempt_at": retry_at(article["rewrite_attempts"]), "rewrite_last_error": "rewrite_attempt_failed"}
                result["errors"] += 1
            await self.db.articles.update_one(selector, {"$set": fields, "$unset": {"rewrite_token": "", "rewrite_lease_until": ""}})
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
