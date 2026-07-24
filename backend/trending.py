"""
TransferNews.de - Enhanced Trending & Breaking News Engine
Erweiterte Version mit:
- Präziseres Event-Scoring
- Zeitfenster-basierte Trend-Erkennung (15m, 1h, 6h, 24h)
- SEO-Landingpage Daten für Wettbewerbe und Themen
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import re

logger = logging.getLogger(__name__)

# ========================
# EXTENDED CONSTANTS
# ========================

# Top players with detailed ratings (name -> (popularity, tier))
# Tier 1: Weltklasse, Tier 2: Top-Liga Stars, Tier 3: Bekannte Spieler
TOP_PLAYERS = {
    # Tier 1 - Weltklasse (90-100)
    "mbappe": (100, 1), "haaland": (98, 1), "bellingham": (96, 1), 
    "vinicius": (95, 1), "messi": (94, 1), "ronaldo": (93, 1),
    
    # Tier 2 - Top Stars (80-89)
    "salah": (89, 2), "kane": (88, 2), "musiala": (87, 2), "wirtz": (86, 2),
    "saka": (85, 2), "palmer": (84, 2), "rodri": (83, 2), "de bruyne": (82, 2),
    "foden": (81, 2), "pedri": (80, 2),
    
    # Tier 3 - Bekannte Spieler (70-79)
    "sancho": (79, 3), "rashford": (78, 3), "olise": (77, 3), "neymar": (76, 3),
    "lewandowski": (75, 3), "griezmann": (74, 3), "modric": (73, 3),
    "kroos": (72, 3), "müller": (71, 3), "neuer": (70, 3),
    
    # Deutsche Liga Spieler (60-69)
    "füllkrug": (68, 3), "havertz": (67, 3), "gnabry": (66, 3),
    "sané": (65, 3), "gündogan": (64, 3), "ter stegen": (63, 3),
    "kimmich": (62, 3), "goretzka": (61, 3), "brandt": (60, 3)
}

# Top clubs with league tier
# Tier 1: Absolute Top-Clubs, Tier 2: Top-Liga Clubs, Tier 3: Bekannte Clubs
TOP_CLUBS = {
    # Tier 1 - Weltspitze (90-100)
    "real madrid": (100, 1), "barcelona": (98, 1), "manchester city": (97, 1),
    "liverpool": (96, 1), "bayern": (95, 1), "psg": (94, 1),
    "manchester united": (93, 1), "chelsea": (92, 1), "arsenal": (91, 1),
    
    # Tier 2 - Top Clubs (80-89)
    "juventus": (89, 2), "dortmund": (88, 2), "inter": (87, 2),
    "milan": (86, 2), "atletico": (85, 2), "tottenham": (84, 2),
    "napoli": (83, 2), "roma": (82, 2), "newcastle": (81, 2),
    
    # Tier 3 - Bekannte Clubs (70-79)
    "west ham": (79, 3), "aston villa": (78, 3), "brighton": (77, 3),
    "rb leipzig": (76, 3), "leverkusen": (75, 3), "frankfurt": (74, 3),
    "sevilla": (73, 3), "benfica": (72, 3), "porto": (71, 3),
    
    # Bundesliga (60-69)
    "gladbach": (68, 3), "wolfsburg": (67, 3), "freiburg": (66, 3),
    "union berlin": (65, 3), "hoffenheim": (64, 3), "mainz": (63, 3),
    "köln": (62, 3), "augsburg": (61, 3), "stuttgart": (60, 3)
}

# Source reliability scores with categories
SOURCE_TRUST = {
    # Tier 1 - Höchst vertrauenswürdig (90-100)
    "fabrizio romano": (98, "journalist"),
    "official": (100, "official"),  # Offizielle Vereinsmeldungen
    
    # Tier 2 - Sehr vertrauenswürdig (80-89)
    "sky sports": (90, "tv"),
    "sky sport": (90, "tv"),
    "the athletic": (92, "media"),
    "kicker": (88, "media"),
    
    # Tier 3 - Vertrauenswürdig (70-79)
    "bild": (78, "media"),
    "sport1": (80, "media"),
    "transfermarkt": (85, "platform"),
    "espn": (75, "media"),
    "sportbuzzer": (72, "media"),
    
    # Tier 4 - Standard (60-69)
    "goal": (68, "media"),
    "90min": (65, "media"),
    "spox": (70, "media"),
    "fussball.news": (62, "media")
}

# Breaking keywords with weights
BREAKING_KEYWORDS = {
    # Definitiv (100%)
    "offiziell": 25, "official": 25, "bestätigt": 25, "confirmed": 25,
    "here we go": 30, "done deal": 28, "vollzogen": 25,
    
    # Sehr wahrscheinlich (80-90%)
    "unterschrieben": 22, "signed": 22, "agreement": 20,
    "fix": 20, "perfekt": 20, "abgeschlossen": 20,
    
    # Fortgeschritten (60-80%)
    "einigung": 15, "verhandlungen": 12, "negotiations": 12,
    "kurz vor": 15, "close to": 15, "imminent": 18,
    
    # Transfer-Typ Keywords
    "rekordtransfer": 20, "rekordablöse": 20,
    "ablösefrei": 15, "leihe": 10, "loan": 10
}

# Transfer type multipliers
TRANSFER_TYPE_MULTIPLIERS = {
    "permanent": 1.0,
    "loan": 0.7,
    "free": 0.9,
    "swap": 1.1,
    "record": 1.5
}

# Time decay factors (newer = higher score)
TIME_DECAY = {
    "15min": 1.5,    # Letzte 15 Minuten
    "1hour": 1.3,    # Letzte Stunde
    "6hours": 1.1,   # Letzte 6 Stunden
    "24hours": 1.0,  # Letzter Tag
    "older": 0.8     # Älter
}


# ========================
# ENHANCED EVENT SCORING
# ========================

def calculate_event_score(event: dict) -> dict:
    """
    Calculate detailed priority score for an event
    Returns: {score, priority, is_breaking, transfer_probability, reasons, breakdown}
    """
    score = 0
    reasons = []
    breakdown = {
        "player_score": 0,
        "club_score": 0,
        "source_score": 0,
        "keyword_score": 0,
        "time_bonus": 0
    }
    
    headline = event.get("headline_raw", "").lower()
    source = event.get("source", "").lower()
    created_at = event.get("created_at")
    
    # 1. Player Popularity Score (0-35 points)
    best_player_score = 0
    best_player = None
    for player, (pop, tier) in TOP_PLAYERS.items():
        if player in headline:
            player_score = int(pop * 0.35)
            if player_score > best_player_score:
                best_player_score = player_score
                best_player = player
    
    if best_player:
        breakdown["player_score"] = best_player_score
        score += best_player_score
        reasons.append(f"Top-Spieler: {best_player.title()} (+{best_player_score})")
    
    # 2. Club Popularity Score (0-30 points)
    clubs_found = []
    for club, (pop, tier) in TOP_CLUBS.items():
        if club in headline:
            clubs_found.append((club, int(pop * 0.30)))
    
    # Bonus für Transfer zwischen zwei Top-Clubs
    if len(clubs_found) >= 2:
        club_score = sum(c[1] for c in clubs_found[:2])
        breakdown["club_score"] = min(club_score, 45)  # Cap at 45
        score += breakdown["club_score"]
        reasons.append(f"Transfer zwischen: {clubs_found[0][0].title()} & {clubs_found[1][0].title()} (+{breakdown['club_score']})")
    elif len(clubs_found) == 1:
        breakdown["club_score"] = clubs_found[0][1]
        score += breakdown["club_score"]
        reasons.append(f"Top-Club: {clubs_found[0][0].title()} (+{breakdown['club_score']})")
    
    # 3. Source Trust Score (0-25 points)
    for src, (trust, category) in SOURCE_TRUST.items():
        if src in source:
            src_score = int(trust * 0.25)
            breakdown["source_score"] = src_score
            score += src_score
            reasons.append(f"Quelle: {src.title()} ({category}) (+{src_score})")
            break
    
    # 4. Breaking Keywords Score (0-30 points)
    keyword_total = 0
    keywords_found = []
    for keyword, weight in BREAKING_KEYWORDS.items():
        if keyword in headline:
            keyword_total += weight
            keywords_found.append(keyword)
    
    breakdown["keyword_score"] = min(keyword_total, 30)  # Cap at 30
    score += breakdown["keyword_score"]
    if keywords_found:
        reasons.append(f"Keywords: {', '.join(keywords_found[:3])} (+{breakdown['keyword_score']})")
    
    # 5. Time Freshness Bonus (0-15 points)
    if created_at:
        try:
            if isinstance(created_at, str):
                event_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                event_time = created_at
            
            age = datetime.now(timezone.utc) - event_time.replace(tzinfo=timezone.utc)
            
            if age < timedelta(minutes=15):
                breakdown["time_bonus"] = 15
                reasons.append("Brandaktuell (< 15 min) (+15)")
            elif age < timedelta(hours=1):
                breakdown["time_bonus"] = 12
                reasons.append("Sehr aktuell (< 1h) (+12)")
            elif age < timedelta(hours=6):
                breakdown["time_bonus"] = 8
                reasons.append("Aktuell (< 6h) (+8)")
            elif age < timedelta(hours=24):
                breakdown["time_bonus"] = 5
                reasons.append("Heute (+5)")
            
            score += breakdown["time_bonus"]
        except:
            pass
    
    # Calculate priority and is_breaking
    if score >= 80:
        priority = "HIGH"
        is_breaking = True
        transfer_probability = min(95, 50 + score // 2)
    elif score >= 50:
        priority = "MEDIUM"
        is_breaking = score >= 70
        transfer_probability = min(80, 30 + score // 2)
    else:
        priority = "LOW"
        is_breaking = False
        transfer_probability = min(50, 10 + score // 2)
    
    return {
        "score": score,
        "priority": priority,
        "is_breaking": is_breaking,
        "transfer_probability": transfer_probability,
        "reasons": reasons,
        "breakdown": breakdown
    }


def batch_score_events(events: List[dict]) -> List[dict]:
    """Score multiple events and sort by priority"""
    scored = []
    for event in events:
        score_data = calculate_event_score(event)
        event_copy = event.copy()
        event_copy["score_data"] = score_data
        scored.append(event_copy)
    
    # Sort by score descending
    scored.sort(key=lambda x: x["score_data"]["score"], reverse=True)
    return scored


# ========================
# TIME-WINDOW TREND SYSTEM
# ========================

async def get_trend_windows(db: AsyncIOMotorDatabase) -> dict:
    """
    Get trending entities across multiple time windows
    Returns trend data for 15min, 1h, 6h, 24h windows
    """
    now = datetime.now(timezone.utc)
    
    windows = {
        "15min": now - timedelta(minutes=15),
        "1hour": now - timedelta(hours=1),
        "6hours": now - timedelta(hours=6),
        "24hours": now - timedelta(hours=24)
    }
    
    result = {}
    
    for window_name, cutoff in windows.items():
        # Get events in this window
        events = await db.events.find({
            "created_at": {"$gte": cutoff.isoformat()}
        }).to_list(500)
        
        # Count and score entities
        player_data = {}
        club_data = {}
        
        for event in events:
            headline = event.get("headline_raw", "").lower()
            score_data = calculate_event_score(event)
            event_score = score_data["score"]
            
            for player, (pop, tier) in TOP_PLAYERS.items():
                if player in headline:
                    if player not in player_data:
                        player_data[player] = {"count": 0, "total_score": 0, "popularity": pop, "tier": tier}
                    player_data[player]["count"] += 1
                    player_data[player]["total_score"] += event_score
            
            for club, (pop, tier) in TOP_CLUBS.items():
                if club in headline:
                    if club not in club_data:
                        club_data[club] = {"count": 0, "total_score": 0, "popularity": pop, "tier": tier}
                    club_data[club]["count"] += 1
                    club_data[club]["total_score"] += event_score
        
        # Calculate trend scores
        for name, data in player_data.items():
            # Trend score = count * avg_score * time_multiplier
            avg_score = data["total_score"] / data["count"] if data["count"] > 0 else 0
            time_mult = TIME_DECAY.get(window_name, 1.0)
            data["trend_score"] = int(data["count"] * avg_score * time_mult / 10)
        
        for name, data in club_data.items():
            avg_score = data["total_score"] / data["count"] if data["count"] > 0 else 0
            time_mult = TIME_DECAY.get(window_name, 1.0)
            data["trend_score"] = int(data["count"] * avg_score * time_mult / 10)
        
        # Sort by trend score
        sorted_players = sorted(player_data.items(), key=lambda x: -x[1]["trend_score"])[:10]
        sorted_clubs = sorted(club_data.items(), key=lambda x: -x[1]["trend_score"])[:10]
        
        result[window_name] = {
            "players": [{"name": p, **data} for p, data in sorted_players],
            "clubs": [{"name": c, **data} for c, data in sorted_clubs],
            "event_count": len(events)
        }
    
    return result


async def get_trending_entities(db: AsyncIOMotorDatabase, hours: int = 24) -> dict:
    """
    Enhanced trending entities with trend scores
    Falls back to article-based trending if no events found
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Get recent events
    events = await db.events.find({
        "created_at": {"$gte": cutoff.isoformat()}
    }).to_list(500)
    
    # Also check articles for mentions - use longer window for articles
    articles = await db.articles.find({
        "status": "published"
    }, {"_id": 0, "title": 1, "body": 1, "player_name": 1, "from_club": 1, "to_club": 1, "published_at": 1}).sort("published_at", -1).limit(100).to_list(100)
    
    player_data = {}
    club_data = {}
    
    # Process events
    for event in events:
        headline = event.get("headline_raw", "").lower()
        score_data = calculate_event_score(event)
        
        for player, (pop, tier) in TOP_PLAYERS.items():
            if player in headline:
                if player not in player_data:
                    player_data[player] = {"count": 0, "event_score": 0, "article_count": 0}
                player_data[player]["count"] += 1
                player_data[player]["event_score"] += score_data["score"]
        
        for club, (pop, tier) in TOP_CLUBS.items():
            if club in headline:
                if club not in club_data:
                    club_data[club] = {"count": 0, "event_score": 0, "article_count": 0}
                club_data[club]["count"] += 1
                club_data[club]["event_score"] += score_data["score"]
    
    # Process articles - primary source if no events
    for article in articles:
        text = (article.get("title", "") + " " + article.get("body", "")).lower()
        player_name = article.get("player_name", "").lower() if article.get("player_name") else ""
        from_club = article.get("from_club", "").lower() if article.get("from_club") else ""
        to_club = article.get("to_club", "").lower() if article.get("to_club") else ""
        
        # Add player from article metadata
        for player, (pop, tier) in TOP_PLAYERS.items():
            if player in text or player in player_name:
                if player not in player_data:
                    player_data[player] = {"count": 0, "event_score": 0, "article_count": 0, "popularity": pop}
                player_data[player]["article_count"] += 1
                player_data[player]["popularity"] = pop
        
        # Add clubs from article metadata
        for club, (pop, tier) in TOP_CLUBS.items():
            if club in text or club in from_club or club in to_club:
                if club not in club_data:
                    club_data[club] = {"count": 0, "event_score": 0, "article_count": 0, "popularity": pop}
                club_data[club]["article_count"] += 1
                club_data[club]["popularity"] = pop
    
    # Calculate trend scores
    def calc_trend_score(data):
        base = data.get("count", 0) * 10 + data.get("event_score", 0) // 5 + data.get("article_count", 0) * 15
        pop_bonus = data.get("popularity", 50) // 10
        return base + pop_bonus
    
    for name, data in player_data.items():
        data["trend_score"] = calc_trend_score(data)
    
    for name, data in club_data.items():
        data["trend_score"] = calc_trend_score(data)
    
    # Sort and format
    trending_players = sorted(player_data.items(), key=lambda x: -x[1]["trend_score"])[:10]
    trending_clubs = sorted(club_data.items(), key=lambda x: -x[1]["trend_score"])[:10]
    
    # Lookup players in database to get their IDs
    player_results = []
    for p, data in trending_players:
        slug = p.replace(" ", "-")
        # Try to find player in database by slug or alias
        db_player = await db.players.find_one({
            "$or": [
                {"slug": slug},
                {"aliases": {"$regex": f"^{p}$", "$options": "i"}}
            ]
        }, {"_id": 0, "id": 1, "name": 1, "slug": 1, "image": 1})
        
        if db_player:
            player_results.append({
                "id": db_player.get("id"),
                "name": db_player.get("name", p.title()),
                "slug": db_player.get("slug", slug),
                "image": db_player.get("image"),
                **data
            })
        else:
            # No DB entry - item will be non-clickable
            player_results.append({
                "name": p.title(),
                "slug": slug,
                **data
            })
    
    # Lookup clubs in database
    club_results = []
    for c, data in trending_clubs:
        slug = c.replace(" ", "-")
        db_club = await db.clubs.find_one({
            "$or": [
                {"slug": slug},
                {"name": {"$regex": f"^{c}$", "$options": "i"}}
            ]
        }, {"_id": 0, "id": 1, "name": 1, "slug": 1, "logo": 1})
        
        if db_club:
            club_results.append({
                "id": db_club.get("id"),
                "name": db_club.get("name", c.title()),
                "slug": db_club.get("slug", slug),
                "logo": db_club.get("logo"),
                **data
            })
        else:
            club_results.append({
                "name": c.title(),
                "slug": slug,
                **data
            })
    
    return {
        "trending_players": player_results,
        "trending_clubs": club_results,
        "period_hours": hours,
        "event_count": len(events),
        "article_count": len(articles)
    }


async def get_breaking_news(db: AsyncIOMotorDatabase, limit: int = 5) -> List[dict]:
    """Get latest breaking news articles"""
    articles = await db.articles.find(
        {"is_breaking": True, "status": "published"},
        {"_id": 0}
    ).sort("published_at", -1).limit(limit).to_list(limit)
    
    return articles


# ========================
# SEO LANDING PAGE DATA
# ========================

# Competition mappings
COMPETITIONS = {
    "bundesliga": {
        "name": "Bundesliga",
        "country": "Deutschland",
        "code": "BL1",
        "clubs": ["bayern", "dortmund", "rb leipzig", "leverkusen", "frankfurt", "gladbach", "wolfsburg", "freiburg", "union berlin", "hoffenheim", "mainz", "köln", "augsburg", "stuttgart"]
    },
    "premier-league": {
        "name": "Premier League",
        "country": "England",
        "code": "PL",
        "clubs": ["manchester city", "liverpool", "arsenal", "chelsea", "manchester united", "tottenham", "newcastle", "west ham", "aston villa", "brighton"]
    },
    "la-liga": {
        "name": "La Liga",
        "country": "Spanien",
        "code": "PD",
        "clubs": ["real madrid", "barcelona", "atletico", "sevilla"]
    },
    "serie-a": {
        "name": "Serie A",
        "country": "Italien",
        "code": "SA",
        "clubs": ["juventus", "inter", "milan", "napoli", "roma"]
    },
    "ligue-1": {
        "name": "Ligue 1",
        "country": "Frankreich",
        "code": "FL1",
        "clubs": ["psg"]
    },
    "champions-league": {
        "name": "Champions League",
        "country": "Europa",
        "code": "CL",
        "clubs": []  # Top clubs from all leagues
    }
}

# Theme pages
THEMES = {
    "abloesefreie-transfers": {
        "name": "Ablösefreie Transfers",
        "description": "Spieler deren Vertrag ausläuft und die ablösefrei wechseln können",
        "keywords": ["ablösefrei", "vertragsende", "auslaufend", "free agent", "vertrag läuft aus"]
    },
    "deadline-day": {
        "name": "Deadline Day",
        "description": "Alle Transfers am letzten Tag der Transferperiode",
        "keywords": ["deadline", "letzter tag", "transferschluss", "last minute"]
    },
    "sommertransfers": {
        "name": "Sommer-Transfers 2025",
        "description": "Alle Transfers der Sommer-Transferperiode",
        "keywords": ["sommer", "sommertransfer", "summer"]
    },
    "wintertransfers": {
        "name": "Winter-Transfers 2025",
        "description": "Alle Transfers der Winter-Transferperiode",
        "keywords": ["winter", "wintertransfer", "januar"]
    },
    "rekordtransfers": {
        "name": "Rekordtransfers",
        "description": "Die teuersten Transfers aller Zeiten",
        "keywords": ["rekord", "rekordtransfer", "rekordablöse", "teuerste"]
    },
    "leihen": {
        "name": "Leih-Transfers",
        "description": "Alle aktuellen Leih-Deals",
        "keywords": ["leihe", "ausgeliehen", "loan", "leihgeschäft"]
    },
    "junge-talente": {
        "name": "Junge Talente",
        "description": "Transfer-News zu Nachwuchsspielern und Wonderkids",
        "keywords": ["talent", "nachwuchs", "wonderkid", "jugend", "u21", "u19"]
    }
}


async def get_competition_landing_data(db: AsyncIOMotorDatabase, competition_slug: str) -> Optional[dict]:
    """Get all data for competition SEO landing page"""
    
    competition = COMPETITIONS.get(competition_slug)
    if not competition:
        return None
    
    # Build query for clubs in this competition
    club_patterns = [re.escape(club) for club in competition["clubs"]]
    
    if club_patterns:
        regex_pattern = "|".join(club_patterns)
        query = {
            "status": "published",
            "$or": [
                {"title": {"$regex": regex_pattern, "$options": "i"}},
                {"body": {"$regex": regex_pattern, "$options": "i"}}
            ]
        }
    else:
        # For Champions League, get all top club news
        query = {"status": "published"}
    
    articles = await db.articles.find(
        query,
        {"_id": 0}
    ).sort("published_at", -1).limit(50).to_list(50)
    
    # Get clubs from DB
    clubs = await db.clubs.find(
        {"competition_id": competition["code"]},
        {"_id": 0}
    ).to_list(100)
    
    # Categorize articles
    rumours = [a for a in articles if a.get("transfer_status") in ["GERÜCHT", "rumour"]]
    confirmed = [a for a in articles if a.get("transfer_status") in ["BESTÄTIGT", "OFFIZIELL", "confirmed", "official"]]
    breaking = [a for a in articles if a.get("is_breaking")]
    
    return {
        "competition": competition,
        "slug": competition_slug,
        "all_news": articles,
        "breaking_news": breaking[:5],
        "rumours": rumours[:20],
        "confirmed_transfers": confirmed[:20],
        "clubs": clubs,
        "article_count": len(articles),
        "seo": {
            "title": f"{competition['name']} Transfer-News | transfernews.de",
            "description": f"Aktuelle Transfer-News, Gerüchte und bestätigte Wechsel aus der {competition['name']}. Alle Transfers im Überblick.",
            "h1": f"{competition['name']} Transfer-News"
        }
    }


async def get_theme_landing_data(db: AsyncIOMotorDatabase, theme_slug: str) -> Optional[dict]:
    """Get all data for theme SEO landing page"""
    
    theme = THEMES.get(theme_slug)
    if not theme:
        return None
    
    # Build query from keywords
    keyword_patterns = [re.escape(kw) for kw in theme["keywords"]]
    regex_pattern = "|".join(keyword_patterns)
    
    query = {
        "status": "published",
        "$or": [
            {"title": {"$regex": regex_pattern, "$options": "i"}},
            {"body": {"$regex": regex_pattern, "$options": "i"}}
        ]
    }
    
    articles = await db.articles.find(
        query,
        {"_id": 0}
    ).sort("published_at", -1).limit(50).to_list(50)
    
    # Categorize
    breaking = [a for a in articles if a.get("is_breaking")]
    
    return {
        "theme": theme,
        "slug": theme_slug,
        "all_news": articles,
        "breaking_news": breaking[:5],
        "article_count": len(articles),
        "seo": {
            "title": f"{theme['name']} | transfernews.de",
            "description": theme["description"],
            "h1": theme["name"]
        }
    }


async def get_player_landing_data(db: AsyncIOMotorDatabase, player_slug: str) -> Optional[dict]:
    """Get all data for player landing page"""
    player = await db.players.find_one({"slug": player_slug}, {"_id": 0})
    
    if not player:
        return None
    
    player_name = player.get("name", "")
    
    articles = await db.articles.find(
        {"$or": [
            {"title": {"$regex": player_name, "$options": "i"}},
            {"body": {"$regex": player_name, "$options": "i"}}
        ], "status": "published"},
        {"_id": 0}
    ).sort("published_at", -1).limit(30).to_list(30)
    
    rumours = [a for a in articles if a.get("transfer_status") in ["GERÜCHT", "rumour"]]
    confirmed = [a for a in articles if a.get("transfer_status") in ["BESTÄTIGT", "OFFIZIELL", "confirmed", "official"]]
    
    return {
        "player": player,
        "all_news": articles,
        "rumours": rumours,
        "confirmed_transfers": confirmed,
        "article_count": len(articles),
        "seo": {
            "title": f"{player_name} Transfer-News | transfernews.de",
            "description": f"Aktuelle Transfer-Gerüchte und News zu {player_name}. Wechselt {player_name}? Alle Infos hier.",
            "h1": f"{player_name} Transfer-News"
        }
    }


async def get_club_landing_data(db: AsyncIOMotorDatabase, club_slug: str) -> Optional[dict]:
    """Get all data for club landing page"""
    club = await db.clubs.find_one({"slug": club_slug}, {"_id": 0})
    
    if not club:
        return None
    
    club_name = club.get("name", "")
    
    articles = await db.articles.find(
        {"$or": [
            {"title": {"$regex": club_name, "$options": "i"}},
            {"body": {"$regex": club_name, "$options": "i"}}
        ], "status": "published"},
        {"_id": 0}
    ).sort("published_at", -1).limit(40).to_list(40)
    
    incoming = [a for a in articles if any(kw in a.get("title", "").lower() for kw in ["verpflichtet", "holt", "kommt", "wechselt zu"])]
    outgoing = [a for a in articles if any(kw in a.get("title", "").lower() for kw in ["verlässt", "wechselt von", "geht"])]
    
    return {
        "club": club,
        "all_news": articles,
        "incoming_transfers": incoming,
        "outgoing_transfers": outgoing,
        "article_count": len(articles),
        "seo": {
            "title": f"{club_name} Transfer-News | transfernews.de",
            "description": f"Alle Transfers und Gerüchte rund um {club_name}. Wer kommt, wer geht?",
            "h1": f"{club_name} Transfer-News"
        }
    }


async def get_free_transfers(db: AsyncIOMotorDatabase) -> List[dict]:
    """Get articles about free transfers"""
    return await db.articles.find(
        {"$or": [
            {"title": {"$regex": "ablösefrei", "$options": "i"}},
            {"body": {"$regex": "ablösefrei", "$options": "i"}},
            {"title": {"$regex": "vertragsende", "$options": "i"}}
        ], "status": "published"},
        {"_id": 0}
    ).sort("published_at", -1).limit(50).to_list(50)


async def get_top_transfers(db: AsyncIOMotorDatabase, limit: int = 20) -> List[dict]:
    """Get highest-probability transfer news"""
    return await db.articles.find(
        {"transfer_probability": {"$gte": 70}, "status": "published"},
        {"_id": 0}
    ).sort("published_at", -1).limit(limit).to_list(limit)


# ========================
# INTERNAL LINKING
# ========================

def generate_related_links(article: dict) -> List[dict]:
    """Generate related article links based on entities"""
    text = (article.get("title", "") + " " + article.get("body", "")).lower()
    
    links = []
    
    # Find players
    for player, (pop, tier) in TOP_PLAYERS.items():
        if player in text and len(links) < 3:
            links.append({
                "type": "player",
                "name": player.title(),
                "url": f"/spieler/{player.replace(' ', '-')}",
                "popularity": pop
            })
    
    # Find clubs
    for club, (pop, tier) in TOP_CLUBS.items():
        if club in text and len(links) < 5:
            links.append({
                "type": "club",
                "name": club.title(),
                "url": f"/verein/{club.replace(' ', '-')}",
                "popularity": pop
            })
    
    # Sort by popularity
    links.sort(key=lambda x: -x.get("popularity", 0))
    
    return links[:5]


def get_available_competitions() -> List[dict]:
    """Get list of all available competitions for navigation"""
    return [
        {"slug": slug, "name": data["name"], "country": data["country"]}
        for slug, data in COMPETITIONS.items()
    ]


def get_available_themes() -> List[dict]:
    """Get list of all available themes for navigation"""
    return [
        {"slug": slug, "name": data["name"], "description": data["description"]}
        for slug, data in THEMES.items()
    ]
