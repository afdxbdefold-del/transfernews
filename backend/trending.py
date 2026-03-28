"""
Trending & Breaking News Engine for transfernews.de
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

# ========================
# CONSTANTS
# ========================

# Top players by popularity (extend as needed)
TOP_PLAYERS = {
    "mbappe": 100, "haaland": 98, "bellingham": 95, "vinicius": 93,
    "salah": 92, "messi": 90, "ronaldo": 89, "kane": 88,
    "musiala": 87, "wirtz": 86, "saka": 85, "palmer": 84,
    "rodri": 83, "de bruyne": 82, "sancho": 80, "rashford": 78,
    "olise": 77, "neymar": 76, "lewandowski": 75
}

# Top clubs by popularity
TOP_CLUBS = {
    "real madrid": 100, "barcelona": 98, "manchester city": 97,
    "liverpool": 96, "bayern": 95, "psg": 94, "manchester united": 93,
    "chelsea": 92, "arsenal": 91, "juventus": 90, "dortmund": 88,
    "inter": 85, "milan": 84, "atletico": 83, "tottenham": 82
}

# Source trust scores
SOURCE_TRUST = {
    "fabrizio romano": 95, "sky sports": 90, "bild": 85,
    "sport1": 85, "kicker": 90, "transfermarkt": 88,
    "the athletic": 92, "espn": 80, "goal": 75
}

# Breaking keywords
BREAKING_KEYWORDS = [
    "offiziell", "bestätigt", "unterschrieben", "deal done", "here we go",
    "vollzogen", "fix", "perfekt", "abgeschlossen", "wechselt"
]

# ========================
# EVENT SCORING
# ========================

def calculate_event_score(event: dict) -> dict:
    """
    Calculate priority score for an event
    Returns: {score, priority, is_breaking, reasons}
    """
    score = 0
    reasons = []
    
    headline = event.get("headline_raw", "").lower()
    source = event.get("source", "").lower()
    
    # 1. Player popularity (0-30 points)
    for player, pop in TOP_PLAYERS.items():
        if player in headline:
            player_score = int(pop * 0.3)
            score += player_score
            reasons.append(f"Top-Spieler: {player} (+{player_score})")
            break
    
    # 2. Club popularity (0-25 points)
    for club, pop in TOP_CLUBS.items():
        if club in headline:
            club_score = int(pop * 0.25)
            score += club_score
            reasons.append(f"Top-Club: {club} (+{club_score})")
            break
    
    # 3. Source trust (0-25 points)
    for src, trust in SOURCE_TRUST.items():
        if src in source:
            src_score = int(trust * 0.25)
            score += src_score
            reasons.append(f"Vertrauenswürdige Quelle: {src} (+{src_score})")
            break
    
    # 4. Breaking keywords (0-20 points)
    for keyword in BREAKING_KEYWORDS:
        if keyword in headline:
            score += 20
            reasons.append(f"Breaking Keyword: {keyword} (+20)")
            break
    
    # Determine priority
    if score >= 70:
        priority = "HIGH"
        is_breaking = True
    elif score >= 40:
        priority = "MEDIUM"
        is_breaking = False
    else:
        priority = "LOW"
        is_breaking = False
    
    return {
        "score": score,
        "priority": priority,
        "is_breaking": is_breaking,
        "reasons": reasons
    }


# ========================
# TREND DETECTION
# ========================

async def get_trending_entities(db: AsyncIOMotorDatabase, hours: int = 24) -> dict:
    """
    Detect trending players and clubs based on event frequency
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Get recent events
    events = await db.events.find({
        "created_at": {"$gte": cutoff.isoformat()}
    }).to_list(500)
    
    # Count entity mentions
    player_counts = {}
    club_counts = {}
    
    for event in events:
        headline = event.get("headline_raw", "").lower()
        
        for player in TOP_PLAYERS:
            if player in headline:
                player_counts[player] = player_counts.get(player, 0) + 1
        
        for club in TOP_CLUBS:
            if club in headline:
                club_counts[club] = club_counts.get(club, 0) + 1
    
    # Sort by count
    trending_players = sorted(player_counts.items(), key=lambda x: -x[1])[:10]
    trending_clubs = sorted(club_counts.items(), key=lambda x: -x[1])[:10]
    
    return {
        "trending_players": [{"name": p, "count": c} for p, c in trending_players],
        "trending_clubs": [{"name": c, "count": cnt} for c, cnt in trending_clubs],
        "period_hours": hours
    }


async def get_breaking_news(db: AsyncIOMotorDatabase, limit: int = 5) -> List[dict]:
    """
    Get latest breaking news articles
    """
    articles = await db.articles.find(
        {"is_breaking": True, "status": "published"},
        {"_id": 0}
    ).sort("published_at", -1).limit(limit).to_list(limit)
    
    return articles


# ========================
# DUPLICATE DETECTION
# ========================

async def find_existing_transfer(db: AsyncIOMotorDatabase, player_name: str, club_name: str = None) -> Optional[dict]:
    """
    Find existing article about same transfer to update instead of duplicate
    """
    query = {"title": {"$regex": player_name, "$options": "i"}}
    
    if club_name:
        query["$or"] = [
            {"title": {"$regex": club_name, "$options": "i"}},
            {"body": {"$regex": club_name, "$options": "i"}}
        ]
    
    existing = await db.articles.find_one(query, {"_id": 0})
    return existing


async def update_transfer_status(db: AsyncIOMotorDatabase, article_id: str, new_status: str, new_probability: int, additional_info: str = None) -> bool:
    """
    Update existing article with new status instead of creating duplicate
    """
    status_map = {
        "rumour": "GERÜCHT",
        "advanced": "FORTGESCHRITTEN", 
        "confirmed": "BESTÄTIGT",
        "official": "OFFIZIELL"
    }
    
    update = {
        "$set": {
            "transfer_status": status_map.get(new_status, new_status),
            "transfer_probability": new_probability,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    }
    
    if additional_info:
        update["$push"] = {"update_history": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "info": additional_info
        }}
    
    result = await db.articles.update_one({"id": article_id}, update)
    return result.modified_count > 0


# ========================
# SEO LANDING PAGE DATA
# ========================

async def get_player_landing_data(db: AsyncIOMotorDatabase, player_slug: str) -> dict:
    """
    Get all data for player landing page
    """
    # Find player
    player = await db.players.find_one({"slug": player_slug}, {"_id": 0})
    
    if not player:
        return None
    
    player_name = player.get("name", "")
    
    # Get related articles
    articles = await db.articles.find(
        {"$or": [
            {"title": {"$regex": player_name, "$options": "i"}},
            {"body": {"$regex": player_name, "$options": "i"}}
        ]},
        {"_id": 0}
    ).sort("published_at", -1).limit(20).to_list(20)
    
    # Separate by type
    rumours = [a for a in articles if a.get("transfer_status") == "GERÜCHT"]
    confirmed = [a for a in articles if a.get("transfer_status") in ["BESTÄTIGT", "OFFIZIELL"]]
    
    return {
        "player": player,
        "all_news": articles,
        "rumours": rumours,
        "confirmed_transfers": confirmed,
        "article_count": len(articles)
    }


async def get_club_landing_data(db: AsyncIOMotorDatabase, club_slug: str) -> dict:
    """
    Get all data for club landing page
    """
    club = await db.clubs.find_one({"slug": club_slug}, {"_id": 0})
    
    if not club:
        return None
    
    club_name = club.get("name", "")
    
    articles = await db.articles.find(
        {"$or": [
            {"title": {"$regex": club_name, "$options": "i"}},
            {"body": {"$regex": club_name, "$options": "i"}}
        ]},
        {"_id": 0}
    ).sort("published_at", -1).limit(30).to_list(30)
    
    incoming = [a for a in articles if "verpflichtet" in a.get("title", "").lower() or "holt" in a.get("title", "").lower()]
    outgoing = [a for a in articles if "verlässt" in a.get("title", "").lower() or "wechselt" in a.get("title", "").lower()]
    
    return {
        "club": club,
        "all_news": articles,
        "incoming_transfers": incoming,
        "outgoing_transfers": outgoing,
        "article_count": len(articles)
    }


# ========================
# AUTOMATIC PAGES DATA
# ========================

async def get_free_transfers(db: AsyncIOMotorDatabase) -> List[dict]:
    """Get articles about free transfers"""
    return await db.articles.find(
        {"$or": [
            {"title": {"$regex": "ablösefrei", "$options": "i"}},
            {"body": {"$regex": "ablösefrei", "$options": "i"}},
            {"title": {"$regex": "vertragsende", "$options": "i"}}
        ]},
        {"_id": 0}
    ).sort("published_at", -1).limit(50).to_list(50)


async def get_top_transfers(db: AsyncIOMotorDatabase, limit: int = 20) -> List[dict]:
    """Get highest-scored transfer news"""
    return await db.articles.find(
        {"transfer_probability": {"$gte": 80}},
        {"_id": 0}
    ).sort("published_at", -1).limit(limit).to_list(limit)


# ========================
# INTERNAL LINKING
# ========================

def extract_entities_for_linking(text: str) -> dict:
    """
    Extract player and club names from text for internal linking
    """
    text_lower = text.lower()
    
    found_players = []
    found_clubs = []
    
    for player in TOP_PLAYERS:
        if player in text_lower:
            found_players.append(player)
    
    for club in TOP_CLUBS:
        if club in text_lower:
            found_clubs.append(club)
    
    return {
        "players": found_players,
        "clubs": found_clubs
    }


def generate_related_links(article: dict) -> List[dict]:
    """
    Generate related article links based on entities
    """
    entities = extract_entities_for_linking(article.get("title", "") + " " + article.get("body", ""))
    
    links = []
    
    for player in entities["players"][:2]:
        links.append({
            "type": "player",
            "name": player.title(),
            "url": f"/spieler/{player.replace(' ', '-')}"
        })
    
    for club in entities["clubs"][:2]:
        links.append({
            "type": "club", 
            "name": club.title(),
            "url": f"/verein/{club.replace(' ', '-')}"
        })
    
    return links
