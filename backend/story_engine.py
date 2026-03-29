"""
TRANSFER NEWS – STORY ENGINE
=============================
Duplicate Killer + Source Weighting + Stage Detection

Eine Transferstory = eine URL
Mehrere Quellen = Update, nicht neuer Artikel
"""

import re
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger("story_engine")

# =============================================================================
# SOURCE WEIGHTING
# =============================================================================

SOURCE_WEIGHTS = {
    "Sky Sports": {"trust": 9.5, "speed": 9.0, "region": "uk", "tier": 1},
    "CaughtOffside": {"trust": 7.0, "speed": 8.5, "region": "global", "tier": 1},
    "90min": {"trust": 6.8, "speed": 8.0, "region": "global", "tier": 1},
    "FootballTransfers": {"trust": 6.5, "speed": 7.2, "region": "global", "tier": 2},
    "Goal": {"trust": 7.2, "speed": 7.0, "region": "global", "tier": 2},
    "Marca": {"trust": 8.8, "speed": 8.8, "region": "spain", "tier": 1},
    "AS": {"trust": 8.0, "speed": 8.0, "region": "spain", "tier": 2},
    "Mundo Deportivo": {"trust": 7.8, "speed": 7.8, "region": "spain", "tier": 2},
    "Gazzetta dello Sport": {"trust": 8.7, "speed": 8.4, "region": "italy", "tier": 1},
    "Corriere dello Sport": {"trust": 8.0, "speed": 7.9, "region": "italy", "tier": 2},
    "Tuttosport": {"trust": 7.6, "speed": 7.7, "region": "italy", "tier": 2},
    "L'Équipe": {"trust": 9.0, "speed": 8.3, "region": "france", "tier": 1},
    "RMC Sport": {"trust": 8.3, "speed": 8.2, "region": "france", "tier": 2},
    "Foot Mercato": {"trust": 7.5, "speed": 8.4, "region": "france", "tier": 2},
    "BILD": {"trust": 7.8, "speed": 8.7, "region": "germany", "tier": 1},
    "kicker": {"trust": 9.0, "speed": 6.8, "region": "germany", "tier": 2},
    "Sport1": {"trust": 7.4, "speed": 7.5, "region": "germany", "tier": 2},
    "BBC Sport": {"trust": 8.7, "speed": 6.9, "region": "uk", "tier": 2},
    "TEAMtalk": {"trust": 6.7, "speed": 7.3, "region": "uk", "tier": 2},
}

# Country bonus: lokale Quellen für lokale Stories bevorzugen
COUNTRY_BONUS_SOURCES = {
    "spain": ["Marca", "AS", "Mundo Deportivo"],
    "italy": ["Gazzetta dello Sport", "Corriere dello Sport", "Tuttosport"],
    "france": ["L'Équipe", "RMC Sport", "Foot Mercato"],
    "germany": ["BILD", "kicker", "Sport1"],
    "uk": ["Sky Sports", "BBC Sport", "TEAMtalk"],
}

# =============================================================================
# STAGE DETECTION
# =============================================================================

STAGE_KEYWORDS = {
    "official": [
        "official", "confirmed", "announced", "has signed", "completed the signing",
        "club statement", "offiziell", "bestätigt", "unterschrieben", "verpflichtet",
        "ufficiale", "oficial", "officiel"
    ],
    "done": [
        "here we go", "deal done", "full agreement", "agreement reached",
        "set to join", "will sign", "perfekt", "fix", "done deal",
        "accordo totale", "acuerdo cerrado", "accord trouvé"
    ],
    "near_done": [
        "advanced talks", "final details", "medical scheduled", "medical booked",
        "closing in", "close to signing", "medizincheck", "kurz vor",
        "visite mediche", "revisión médica", "visite médicale"
    ],
    "advanced": [
        "talks ongoing", "serious interest", "pushing to sign", "working on a deal",
        "in negotiations", "verhandlungen", "gespräche", "trattativa",
        "negociaciones", "négociations"
    ],
    "rumor": [
        "linked with", "interested in", "monitoring", "considering",
        "could move", "targeting", "gerücht", "interesse", "beobachtet",
        "rumor", "rumeur", "voce"
    ]
}

STAGE_RANK = {
    "rumor": 1,
    "advanced": 2,
    "near_done": 3,
    "done": 4,
    "official": 5
}

# =============================================================================
# TRANSFER TYPE DETECTION
# =============================================================================

TRANSFER_TYPE_KEYWORDS = {
    "permanent": [
        "permanent", "buy", "purchase", "fee", "ablöse", "transfer fee",
        "millionen", "millions", "acquisto", "fichaje", "achat"
    ],
    "loan": [
        "loan", "leihe", "leihgeschäft", "prestito", "cesión", "prêt",
        "on loan", "temporary"
    ],
    "free": [
        "free transfer", "ablösefrei", "free agent", "contract expired",
        "parametro zero", "libre", "fin de contrat"
    ],
    "extension": [
        "extension", "renewal", "verlängerung", "new contract", "rinnovo",
        "renovación", "prolongation"
    ]
}

# =============================================================================
# CONFIDENCE SCORING
# =============================================================================

CONFIDENCE_BASE = {
    "rumor": 35,
    "advanced": 50,
    "near_done": 68,
    "done": 85,
    "official": 100
}

# =============================================================================
# HEADLINE TEMPLATES (German)
# =============================================================================

HEADLINE_TEMPLATES = {
    "rumor": "{player} wird mit {club} in Verbindung gebracht",
    "advanced": "{club} arbeitet an Transfer von {player}",
    "near_done": "{player} vor Wechsel zu {club}",
    "done": "{player} steht vor Unterschrift bei {club}",
    "official": "{club} bestätigt Transfer von {player}"
}

# =============================================================================
# SYSTEM DEFAULTS
# =============================================================================

STORY_ACTIVE_WINDOW_HOURS = 96
PUBLISH_THRESHOLD_CONFIDENCE = 45  # Gesenkt für mehr Artikel
PROMINENT_THRESHOLD_CONFIDENCE = 80
MAX_SOURCES_PER_STORY = 10
MAX_SECONDARY_SOURCES_DISPLAYED = 3


@dataclass
class StorySource:
    """Eine Quelle für eine Story"""
    source_name: str
    source_url: str
    published_at: str
    detected_stage: str
    source_score: float
    is_primary: bool = False
    raw_title: str = ""
    raw_summary: str = ""


@dataclass
class TransferStory:
    """Eine Transfer-Story (kann mehrere Quellen haben)"""
    story_key: str
    player_name: str
    player_slug: str
    current_club: str = ""
    target_club: str = ""
    target_club_slug: str = ""
    transfer_type: str = "permanent"
    current_stage: str = "rumor"
    confidence_score: int = 35
    primary_source: str = ""
    secondary_sources: List[str] = field(default_factory=list)
    sources: List[StorySource] = field(default_factory=list)
    headline: str = ""
    slug: str = ""
    article_id: str = ""
    first_seen_at: str = ""
    last_updated_at: str = ""
    status: str = "active"
    # Zusätzliche Fakten
    transfer_fee: str = ""
    contract_length: str = ""
    story_region: str = "global"


class StoryEngine:
    """
    Hauptklasse für das Story-Management.
    Erkennt Duplikate, gewichtet Quellen, tracked Stages.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    # =========================================================================
    # ENTITY EXTRACTION
    # =========================================================================
    
    def extract_entities(self, title: str, summary: str, source_name: str) -> Dict:
        """
        Extrahiert Spieler, Vereine und Transfer-Typ aus dem Text.
        """
        text = f"{title} {summary}".lower()
        
        # Stage Detection
        stage = self._detect_stage(text)
        
        # Transfer Type Detection
        transfer_type = self._detect_transfer_type(text)
        
        # Transfer Fee Detection
        transfer_fee = self._extract_transfer_fee(text)
        
        return {
            "stage": stage,
            "transfer_type": transfer_type,
            "transfer_fee": transfer_fee,
            "raw_text": text
        }
    
    def _detect_stage(self, text: str) -> str:
        """Erkennt die Transfer-Phase"""
        text_lower = text.lower()
        
        # Prüfe von höchster zu niedrigster Stage
        for stage in ["official", "done", "near_done", "advanced", "rumor"]:
            keywords = STAGE_KEYWORDS.get(stage, [])
            if any(kw.lower() in text_lower for kw in keywords):
                return stage
        
        return "rumor"  # Default
    
    def _detect_transfer_type(self, text: str) -> str:
        """Erkennt den Transfer-Typ"""
        text_lower = text.lower()
        
        for ttype, keywords in TRANSFER_TYPE_KEYWORDS.items():
            if any(kw.lower() in text_lower for kw in keywords):
                return ttype
        
        return "permanent"  # Default
    
    def _extract_transfer_fee(self, text: str) -> str:
        """Extrahiert Ablösesumme aus dem Text"""
        # Patterns für Ablöse
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(?:mio|million|millionen|m)\s*(?:€|euro|eur)',
            r'€\s*(\d+(?:[.,]\d+)?)\s*(?:mio|million|m)',
            r'(\d+(?:[.,]\d+)?)\s*(?:mio|million)\s*(?:pounds|£)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1).replace(",", ".")
                return f"{amount} Mio. €"
        
        return ""
    
    # =========================================================================
    # STORY KEY GENERATION
    # =========================================================================
    
    def generate_story_key(self, player_slug: str, target_club_slug: str, 
                           transfer_type: str = "permanent") -> str:
        """
        Generiert einen eindeutigen Story-Key.
        Format: player-slug__target-club-slug__transfer-type
        """
        return f"{player_slug}__{target_club_slug}__{transfer_type}"
    
    def _slugify(self, text: str) -> str:
        """Konvertiert Text zu URL-freundlichem Slug"""
        if not text:
            return ""
        # Lowercase und Sonderzeichen entfernen
        slug = text.lower().strip()
        slug = re.sub(r'[äÄ]', 'ae', slug)
        slug = re.sub(r'[öÖ]', 'oe', slug)
        slug = re.sub(r'[üÜ]', 'ue', slug)
        slug = re.sub(r'[ß]', 'ss', slug)
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')
    
    # =========================================================================
    # SOURCE SCORING
    # =========================================================================
    
    def calculate_source_score(self, source_name: str, story_region: str = "global") -> float:
        """
        Berechnet den Source Score.
        Formula: trust * 0.7 + speed * 0.3 + bonuses
        """
        weights = SOURCE_WEIGHTS.get(source_name, {"trust": 5.0, "speed": 5.0, "region": "global", "tier": 3})
        
        base_score = weights["trust"] * 0.7 + weights["speed"] * 0.3
        
        # Country Bonus
        if story_region != "global":
            preferred_sources = COUNTRY_BONUS_SOURCES.get(story_region, [])
            if source_name in preferred_sources:
                base_score += 0.5
        
        # Tier Bonus
        if weights.get("tier") == 1:
            base_score += 0.4
        
        return round(base_score, 2)
    
    def get_source_region(self, source_name: str) -> str:
        """Gibt die Region einer Quelle zurück"""
        weights = SOURCE_WEIGHTS.get(source_name, {})
        return weights.get("region", "global")
    
    # =========================================================================
    # CONFIDENCE SCORING
    # =========================================================================
    
    def calculate_confidence(self, stage: str, sources: List[StorySource], 
                            story_region: str = "global") -> int:
        """
        Berechnet den Confidence Score einer Story.
        """
        # Basis nach Stage
        confidence = CONFIDENCE_BASE.get(stage, 35)
        
        # Tier 1 Bonus
        for source in sources:
            source_weights = SOURCE_WEIGHTS.get(source.source_name, {})
            if source_weights.get("tier") == 1:
                confidence += 8
                break  # Nur einmal
        
        # Mehrere Quellen Bonus
        if len(sources) >= 2:
            confidence += 6  # Zweite Quelle
        if len(sources) >= 3:
            confidence += 4  # Dritte Quelle
        
        # Lokale Quelle Bonus
        if story_region != "global":
            preferred = COUNTRY_BONUS_SOURCES.get(story_region, [])
            for source in sources:
                if source.source_name in preferred:
                    confidence += 6
                    break
        
        return min(100, confidence)
    
    # =========================================================================
    # HEADLINE GENERATION
    # =========================================================================
    
    def generate_headline(self, player_name: str, club_name: str, stage: str) -> str:
        """Generiert eine deutsche Headline basierend auf der Stage"""
        template = HEADLINE_TEMPLATES.get(stage, HEADLINE_TEMPLATES["rumor"])
        return template.format(player=player_name, club=club_name)
    
    def generate_story_slug(self, player_slug: str, club_slug: str) -> str:
        """Generiert den URL-Slug für die Story"""
        return f"{player_slug}-vor-wechsel-zu-{club_slug}"
    
    # =========================================================================
    # STORY LOOKUP & MATCHING
    # =========================================================================
    
    async def find_existing_story(self, player_slug: str, target_club_slug: str,
                                   transfer_type: str = "permanent") -> Optional[Dict]:
        """
        Sucht nach einer existierenden aktiven Story.
        """
        story_key = self.generate_story_key(player_slug, target_club_slug, transfer_type)
        
        # Zeitfenster: letzte 96 Stunden
        cutoff = datetime.now(timezone.utc) - timedelta(hours=STORY_ACTIVE_WINDOW_HOURS)
        cutoff_str = cutoff.isoformat()
        
        story = await self.db.transfer_stories.find_one({
            "story_key": story_key,
            "status": "active",
            "last_updated_at": {"$gte": cutoff_str}
        }, {"_id": 0})
        
        return story
    
    async def find_story_by_player_and_club(self, player_name: str, 
                                             target_club: str) -> Optional[Dict]:
        """
        Alternative Suche nach Spieler + Verein (ohne exakten Slug).
        """
        player_slug = self._slugify(player_name)
        club_slug = self._slugify(target_club)
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=STORY_ACTIVE_WINDOW_HOURS)
        
        # Fuzzy Match via Regex
        story = await self.db.transfer_stories.find_one({
            "player_slug": {"$regex": f"^{player_slug[:5]}", "$options": "i"},
            "target_club_slug": {"$regex": f"^{club_slug[:5]}", "$options": "i"},
            "status": "active",
            "last_updated_at": {"$gte": cutoff.isoformat()}
        }, {"_id": 0})
        
        return story
    
    # =========================================================================
    # DECISION LOGIC
    # =========================================================================
    
    async def process_incoming_event(self, event: Dict) -> Dict:
        """
        Hauptlogik: Verarbeitet ein eingehendes Event.
        
        Returns:
            Dict mit action ("create_article", "update_article", "merge_only", "skip")
        """
        title = event.get("title", "")
        summary = event.get("summary", "")
        source_name = event.get("source_name", "")
        source_url = event.get("source_url", "")
        player_name = event.get("player_name", "")
        target_club = event.get("club_name", "")  # Zielverein
        
        if not player_name or not target_club:
            return {"action": "skip", "reason": "missing_entities"}
        
        # 1. Entity Extraction
        entities = self.extract_entities(title, summary, source_name)
        stage = entities["stage"]
        transfer_type = entities["transfer_type"]
        transfer_fee = entities["transfer_fee"]
        
        # 2. Slugs generieren
        player_slug = self._slugify(player_name)
        club_slug = self._slugify(target_club)
        
        # 3. Source Score berechnen
        story_region = self._detect_story_region(player_name, target_club)
        source_score = self.calculate_source_score(source_name, story_region)
        
        # 4. Existierende Story suchen
        existing_story = await self.find_existing_story(player_slug, club_slug, transfer_type)
        
        now = datetime.now(timezone.utc).isoformat()
        
        # 5. Source-Objekt erstellen
        new_source = StorySource(
            source_name=source_name,
            source_url=source_url,
            published_at=now,
            detected_stage=stage,
            source_score=source_score,
            is_primary=False,
            raw_title=title,
            raw_summary=summary
        )
        
        if not existing_story:
            # ========== NEUE STORY ==========
            return await self._create_new_story(
                player_name=player_name,
                player_slug=player_slug,
                target_club=target_club,
                club_slug=club_slug,
                transfer_type=transfer_type,
                stage=stage,
                new_source=new_source,
                transfer_fee=transfer_fee,
                story_region=story_region,
                event=event
            )
        else:
            # ========== EXISTIERENDE STORY ==========
            return await self._update_existing_story(
                existing_story=existing_story,
                new_source=new_source,
                new_stage=stage,
                transfer_fee=transfer_fee,
                event=event
            )
    
    def _detect_story_region(self, player_name: str, club_name: str) -> str:
        """Erkennt die Region einer Story basierend auf Verein"""
        club_lower = club_name.lower()
        
        # UK Clubs
        uk_clubs = ["manchester", "liverpool", "chelsea", "arsenal", "tottenham", 
                    "newcastle", "west ham", "aston villa", "everton", "brighton"]
        if any(c in club_lower for c in uk_clubs):
            return "uk"
        
        # Spain
        spain_clubs = ["barcelona", "real madrid", "atletico", "sevilla", "valencia",
                       "villarreal", "real sociedad", "betis"]
        if any(c in club_lower for c in spain_clubs):
            return "spain"
        
        # Italy
        italy_clubs = ["juventus", "inter", "milan", "napoli", "roma", "lazio",
                       "fiorentina", "atalanta", "bologna"]
        if any(c in club_lower for c in italy_clubs):
            return "italy"
        
        # France
        france_clubs = ["psg", "paris", "marseille", "lyon", "monaco", "lille"]
        if any(c in club_lower for c in france_clubs):
            return "france"
        
        # Germany
        germany_clubs = ["bayern", "dortmund", "leipzig", "leverkusen", "frankfurt",
                         "wolfsburg", "gladbach", "stuttgart"]
        if any(c in club_lower for c in germany_clubs):
            return "germany"
        
        return "global"
    
    async def _create_new_story(self, player_name: str, player_slug: str,
                                 target_club: str, club_slug: str,
                                 transfer_type: str, stage: str,
                                 new_source: StorySource, transfer_fee: str,
                                 story_region: str, event: Dict) -> Dict:
        """Erstellt eine neue Story und einen neuen Artikel"""
        
        story_key = self.generate_story_key(player_slug, club_slug, transfer_type)
        now = datetime.now(timezone.utc).isoformat()
        
        # Primary Source setzen
        new_source.is_primary = True
        
        # Confidence berechnen
        confidence = self.calculate_confidence(stage, [new_source], story_region)
        
        # Headline generieren
        headline = self.generate_headline(player_name, target_club, stage)
        
        # Slug generieren
        slug = self.generate_story_slug(player_slug, club_slug)
        
        # Story-Dokument
        story_doc = {
            "story_key": story_key,
            "player_name": player_name,
            "player_slug": player_slug,
            "current_club": event.get("from_club", ""),
            "target_club": target_club,
            "target_club_slug": club_slug,
            "transfer_type": transfer_type,
            "current_stage": stage,
            "confidence_score": confidence,
            "primary_source": new_source.source_name,
            "secondary_sources": [],
            "sources": [self._source_to_dict(new_source)],
            "headline": headline,
            "slug": slug,
            "article_id": "",  # Wird nach Artikel-Erstellung gesetzt
            "first_seen_at": now,
            "last_updated_at": now,
            "status": "active",
            "transfer_fee": transfer_fee,
            "contract_length": "",
            "story_region": story_region,
            "update_count": 0,
        }
        
        # In DB speichern
        await self.db.transfer_stories.insert_one(story_doc)
        
        logger.info(f"[STORY] NEW: {player_name} → {target_club} ({stage}) "
                   f"[{new_source.source_name}] Confidence: {confidence}")
        
        return {
            "action": "create_article",
            "story_key": story_key,
            "story": story_doc,
            "headline": headline,
            "slug": slug,
            "confidence": confidence,
            "stage": stage,
            "should_publish": confidence >= PUBLISH_THRESHOLD_CONFIDENCE,
            "is_prominent": confidence >= PROMINENT_THRESHOLD_CONFIDENCE
        }
    
    async def _update_existing_story(self, existing_story: Dict,
                                      new_source: StorySource,
                                      new_stage: str,
                                      transfer_fee: str,
                                      event: Dict) -> Dict:
        """Aktualisiert eine existierende Story"""
        
        story_key = existing_story["story_key"]
        current_stage = existing_story["current_stage"]
        current_stage_rank = STAGE_RANK.get(current_stage, 1)
        new_stage_rank = STAGE_RANK.get(new_stage, 1)
        
        sources = existing_story.get("sources", [])
        
        # Prüfe ob Quelle schon vorhanden
        source_names = [s.get("source_name") for s in sources]
        if new_source.source_name in source_names:
            logger.debug(f"[STORY] Source already exists: {new_source.source_name}")
            return {"action": "skip", "reason": "source_already_exists"}
        
        # Source hinzufügen (max 10)
        if len(sources) < MAX_SOURCES_PER_STORY:
            sources.append(self._source_to_dict(new_source))
        
        update_fields = {
            "last_updated_at": datetime.now(timezone.utc).isoformat(),
            "sources": sources,
        }
        
        # Entscheidungslogik
        action = "merge_only"
        should_update_article = False
        
        # Check 1: Stage Upgrade?
        if new_stage_rank > current_stage_rank:
            logger.info(f"[STORY] STAGE UPGRADE: {current_stage} → {new_stage}")
            update_fields["current_stage"] = new_stage
            update_fields["headline"] = self.generate_headline(
                existing_story["player_name"],
                existing_story["target_club"],
                new_stage
            )
            should_update_article = True
            action = "update_article"
        
        # Check 2: Stärkere Quelle?
        primary_source = existing_story.get("primary_source", "")
        primary_score = self.calculate_source_score(
            primary_source, existing_story.get("story_region", "global")
        )
        
        if new_source.source_score > primary_score:
            logger.info(f"[STORY] STRONGER SOURCE: {new_source.source_name} "
                       f"({new_source.source_score}) > {primary_source} ({primary_score})")
            update_fields["primary_source"] = new_source.source_name
            # Alte Primary zu Secondary
            secondary = existing_story.get("secondary_sources", [])
            if primary_source and primary_source not in secondary:
                secondary.append(primary_source)
            update_fields["secondary_sources"] = secondary[:MAX_SECONDARY_SOURCES_DISPLAYED]
            
            # Bei stärkerer Quelle + neue Fakten: Update
            if transfer_fee and not existing_story.get("transfer_fee"):
                update_fields["transfer_fee"] = transfer_fee
                should_update_article = True
                action = "update_article"
        else:
            # Schwächere Quelle → nur als Secondary
            secondary = existing_story.get("secondary_sources", [])
            if new_source.source_name not in secondary:
                secondary.append(new_source.source_name)
            update_fields["secondary_sources"] = secondary[:MAX_SECONDARY_SOURCES_DISPLAYED]
        
        # Check 3: Neue Fakten (Fee, Medical, etc.)?
        if transfer_fee and not existing_story.get("transfer_fee"):
            update_fields["transfer_fee"] = transfer_fee
            should_update_article = True
            action = "update_article"
        
        # Confidence neu berechnen
        story_sources = [StorySource(**s) if isinstance(s, dict) else s for s in sources]
        new_confidence = self.calculate_confidence(
            update_fields.get("current_stage", current_stage),
            story_sources,
            existing_story.get("story_region", "global")
        )
        update_fields["confidence_score"] = new_confidence
        
        # Update Count
        if should_update_article:
            update_fields["update_count"] = existing_story.get("update_count", 0) + 1
        
        # DB Update
        await self.db.transfer_stories.update_one(
            {"story_key": story_key},
            {"$set": update_fields}
        )
        
        logger.info(f"[STORY] {action.upper()}: {existing_story['player_name']} "
                   f"[{new_source.source_name}] Stage: {new_stage} Confidence: {new_confidence}")
        
        return {
            "action": action,
            "story_key": story_key,
            "story": {**existing_story, **update_fields},
            "article_id": existing_story.get("article_id"),
            "should_update_article": should_update_article,
            "confidence": new_confidence,
            "stage": update_fields.get("current_stage", current_stage),
            "headline": update_fields.get("headline", existing_story.get("headline")),
        }
    
    def _source_to_dict(self, source: StorySource) -> Dict:
        """Konvertiert StorySource zu Dict für MongoDB"""
        return {
            "source_name": source.source_name,
            "source_url": source.source_url,
            "published_at": source.published_at,
            "detected_stage": source.detected_stage,
            "source_score": source.source_score,
            "is_primary": source.is_primary,
            "raw_title": source.raw_title,
            "raw_summary": source.raw_summary,
        }
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    async def get_story_stats(self) -> Dict:
        """Gibt Statistiken über Stories zurück"""
        total = await self.db.transfer_stories.count_documents({})
        active = await self.db.transfer_stories.count_documents({"status": "active"})
        
        by_stage = {}
        for stage in STAGE_RANK.keys():
            count = await self.db.transfer_stories.count_documents({"current_stage": stage})
            by_stage[stage] = count
        
        return {
            "total_stories": total,
            "active_stories": active,
            "by_stage": by_stage
        }


# =============================================================================
# SINGLETON
# =============================================================================

_story_engine: Optional[StoryEngine] = None

def get_story_engine(db: AsyncIOMotorDatabase) -> StoryEngine:
    global _story_engine
    if _story_engine is None:
        _story_engine = StoryEngine(db)
    return _story_engine
