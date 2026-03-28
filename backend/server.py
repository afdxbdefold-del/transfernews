"""
TransferNews.de - Hauptserver
FastAPI Backend für die Fußball-Transfer-News-Plattform
"""

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import re
import asyncio

from models import (
    Player, PlayerCreate, PlayerUpdate,
    Club, ClubCreate, ClubUpdate,
    Competition, CompetitionCreate, CompetitionUpdate,
    Source, SourceCreate, SourceUpdate,
    Event, EventCreate, EventUpdate, EventStatus,
    Transfer, TransferCreate, TransferUpdate,
    Rumour, RumourCreate, RumourUpdate,
    Article, ArticleCreate, ArticleUpdate, ArticleStatus,
    Alias, AliasCreate, EntityType,
    AdSlot, AdSlotCreate, AdSlotUpdate, PageType, DeviceType,
    User, UserCreate, UserUpdate, UserPublic, UserRole,
    Setting, SettingCreate, SettingUpdate,
    TokenResponse, LoginRequest, PaginatedResponse,
    DraftGenerationRequest, DraftGenerationResponse,
    Author, AuthorCreate, AuthorUpdate
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'default_secret_key_change_me')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI(title="TransferNews.de API", version="1.0.0")

# Mount static files directory for images under /api/static
STATIC_DIR = ROOT_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "images").mkdir(exist_ok=True)
app.mount("/api/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CRAWLER DETECTION & PRE-RENDER SERVING
# =============================================================================

# Known search engine crawler User-Agents
CRAWLER_USER_AGENTS = [
    'googlebot',
    'google-inspectiontool',
    'googleother',
    'bingbot',
    'slurp',        # Yahoo
    'duckduckbot',
    'baiduspider',
    'yandexbot',
    'sogou',
    'facebookexternalhit',
    'twitterbot',
    'linkedinbot',
    'whatsapp',
    'telegrambot',
    'applebot',
    'petalbot',
    'semrushbot',
    'ahrefsbot',
    'mj12bot',
]

def is_crawler(user_agent: str) -> bool:
    """Check if the request is from a known crawler"""
    if not user_agent:
        return False
    ua_lower = user_agent.lower()
    return any(crawler in ua_lower for crawler in CRAWLER_USER_AGENTS)


async def trigger_article_prerender(slug: str):
    """
    Background task to pre-render an article after publish
    Non-blocking, runs asynchronously
    """
    try:
        from prerender import prerender_article, prerender_homepage
        
        await prerender_article(slug)
        await prerender_homepage()  # Also refresh homepage
        logger.info(f"[PRERENDER] Article pre-rendered: {slug}")
        
    except Exception as e:
        logger.error(f"[PRERENDER] Failed to pre-render {slug}: {e}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_slug(text: str) -> str:
    """Generate URL-friendly slug from text"""
    slug = text.lower()
    slug = re.sub(r'[äÄ]', 'ae', slug)
    slug = re.sub(r'[öÖ]', 'oe', slug)
    slug = re.sub(r'[üÜ]', 'ue', slug)
    slug = re.sub(r'[ß]', 'ss', slug)
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


def serialize_datetime(doc: dict) -> dict:
    """Convert datetime objects to ISO strings for MongoDB storage"""
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
    return doc


def deserialize_datetime(doc: dict, fields: List[str]) -> dict:
    """Convert ISO strings back to datetime objects"""
    for field in fields:
        if field in doc and isinstance(doc[field], str):
            try:
                doc[field] = datetime.fromisoformat(doc[field])
            except:
                pass
    return doc


def create_token(user_id: str, email: str, role: str) -> str:
    """Create JWT token"""
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Validate JWT token and return user info"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token abgelaufen")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Ungültiger Token")


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin-Rechte erforderlich")
    return current_user


# =============================================================================
# AUTH ROUTES
# =============================================================================

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Admin login"""
    user = await db.users.find_one({"email": request.email}, {"_id": 0})
    if not user or not pwd_context.verify(request.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Konto deaktiviert")
    
    token = create_token(user["id"], user["email"], user["role"])
    return TokenResponse(access_token=token)


@api_router.get("/auth/me", response_model=UserPublic)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    user = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    return user


# =============================================================================
# USER ROUTES (Admin only)
# =============================================================================

@api_router.post("/users", response_model=UserPublic)
async def create_user(user_data: UserCreate, current_user: dict = Depends(require_admin)):
    """Create new user"""
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="E-Mail bereits registriert")
    
    user = User(
        **user_data.model_dump(exclude={"password"}),
        password_hash=pwd_context.hash(user_data.password)
    )
    doc = serialize_datetime(user.model_dump())
    await db.users.insert_one(doc)
    return UserPublic(**user.model_dump())


@api_router.get("/users", response_model=List[UserPublic])
async def get_users(current_user: dict = Depends(require_admin)):
    """Get all users"""
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users


# =============================================================================
# PLAYER ROUTES
# =============================================================================

@api_router.post("/players", response_model=Player)
async def create_player(player_data: PlayerCreate, current_user: dict = Depends(get_current_user)):
    """Create new player"""
    player = Player(**player_data.model_dump())
    doc = serialize_datetime(player.model_dump())
    await db.players.insert_one(doc)
    return player


@api_router.get("/players", response_model=List[Player])
async def get_players(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None
):
    """Get all players with optional search"""
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"aliases": {"$regex": search, "$options": "i"}}
        ]
    players = await db.players.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return players


@api_router.get("/players/{player_id}", response_model=Player)
async def get_player(player_id: str):
    """Get player by ID"""
    player = await db.players.find_one({"id": player_id}, {"_id": 0})
    if not player:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    return player


@api_router.get("/players/slug/{slug}", response_model=Player)
async def get_player_by_slug(slug: str):
    """Get player by slug"""
    player = await db.players.find_one({"slug": slug}, {"_id": 0})
    if not player:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    return player


@api_router.put("/players/{player_id}", response_model=Player)
async def update_player(player_id: str, player_data: PlayerUpdate, current_user: dict = Depends(get_current_user)):
    """Update player"""
    update_data = {k: v for k, v in player_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.players.update_one({"id": player_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    return await db.players.find_one({"id": player_id}, {"_id": 0})


@api_router.delete("/players/{player_id}")
async def delete_player(player_id: str, current_user: dict = Depends(require_admin)):
    """Delete player"""
    result = await db.players.delete_one({"id": player_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    return {"message": "Spieler gelöscht"}


# =============================================================================
# CLUB ROUTES
# =============================================================================

@api_router.post("/clubs", response_model=Club)
async def create_club(club_data: ClubCreate, current_user: dict = Depends(get_current_user)):
    """Create new club"""
    club = Club(**club_data.model_dump())
    doc = serialize_datetime(club.model_dump())
    await db.clubs.insert_one(doc)
    return club


@api_router.get("/clubs", response_model=List[Club])
async def get_clubs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    competition_id: Optional[str] = None
):
    """Get all clubs with optional search"""
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"aliases": {"$regex": search, "$options": "i"}}
        ]
    if competition_id:
        query["competition_id"] = competition_id
    clubs = await db.clubs.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return clubs


@api_router.get("/clubs/{club_id}", response_model=Club)
async def get_club(club_id: str):
    """Get club by ID"""
    club = await db.clubs.find_one({"id": club_id}, {"_id": 0})
    if not club:
        raise HTTPException(status_code=404, detail="Verein nicht gefunden")
    return club


@api_router.get("/clubs/slug/{slug}", response_model=Club)
async def get_club_by_slug(slug: str):
    """Get club by slug"""
    club = await db.clubs.find_one({"slug": slug}, {"_id": 0})
    if not club:
        raise HTTPException(status_code=404, detail="Verein nicht gefunden")
    return club


@api_router.put("/clubs/{club_id}", response_model=Club)
async def update_club(club_id: str, club_data: ClubUpdate, current_user: dict = Depends(get_current_user)):
    """Update club"""
    update_data = {k: v for k, v in club_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.clubs.update_one({"id": club_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Verein nicht gefunden")
    return await db.clubs.find_one({"id": club_id}, {"_id": 0})


@api_router.delete("/clubs/{club_id}")
async def delete_club(club_id: str, current_user: dict = Depends(require_admin)):
    """Delete club"""
    result = await db.clubs.delete_one({"id": club_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Verein nicht gefunden")
    return {"message": "Verein gelöscht"}


# =============================================================================
# COMPETITION ROUTES
# =============================================================================

@api_router.post("/competitions", response_model=Competition)
async def create_competition(competition_data: CompetitionCreate, current_user: dict = Depends(get_current_user)):
    """Create new competition"""
    competition = Competition(**competition_data.model_dump())
    doc = serialize_datetime(competition.model_dump())
    await db.competitions.insert_one(doc)
    return competition


@api_router.get("/competitions", response_model=List[Competition])
async def get_competitions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None
):
    """Get all competitions"""
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    competitions = await db.competitions.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return competitions


@api_router.get("/competitions/{competition_id}", response_model=Competition)
async def get_competition(competition_id: str):
    """Get competition by ID"""
    competition = await db.competitions.find_one({"id": competition_id}, {"_id": 0})
    if not competition:
        raise HTTPException(status_code=404, detail="Wettbewerb nicht gefunden")
    return competition


@api_router.get("/competitions/slug/{slug}", response_model=Competition)
async def get_competition_by_slug(slug: str):
    """Get competition by slug"""
    competition = await db.competitions.find_one({"slug": slug}, {"_id": 0})
    if not competition:
        raise HTTPException(status_code=404, detail="Wettbewerb nicht gefunden")
    return competition


@api_router.put("/competitions/{competition_id}", response_model=Competition)
async def update_competition(competition_id: str, competition_data: CompetitionUpdate, current_user: dict = Depends(get_current_user)):
    """Update competition"""
    update_data = {k: v for k, v in competition_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.competitions.update_one({"id": competition_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Wettbewerb nicht gefunden")
    return await db.competitions.find_one({"id": competition_id}, {"_id": 0})


@api_router.delete("/competitions/{competition_id}")
async def delete_competition(competition_id: str, current_user: dict = Depends(require_admin)):
    """Delete competition"""
    result = await db.competitions.delete_one({"id": competition_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Wettbewerb nicht gefunden")
    return {"message": "Wettbewerb gelöscht"}


# =============================================================================
# SOURCE ROUTES
# =============================================================================

@api_router.post("/sources", response_model=Source)
async def create_source(source_data: SourceCreate, current_user: dict = Depends(get_current_user)):
    """Create new source"""
    source = Source(**source_data.model_dump())
    doc = serialize_datetime(source.model_dump())
    await db.sources.insert_one(doc)
    return source


@api_router.get("/sources", response_model=List[Source])
async def get_sources(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = False
):
    """Get all sources"""
    query = {"active": True} if active_only else {}
    sources = await db.sources.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return sources


@api_router.get("/sources/{source_id}", response_model=Source)
async def get_source(source_id: str):
    """Get source by ID"""
    source = await db.sources.find_one({"id": source_id}, {"_id": 0})
    if not source:
        raise HTTPException(status_code=404, detail="Quelle nicht gefunden")
    return source


@api_router.put("/sources/{source_id}", response_model=Source)
async def update_source(source_id: str, source_data: SourceUpdate, current_user: dict = Depends(get_current_user)):
    """Update source"""
    update_data = {k: v for k, v in source_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.sources.update_one({"id": source_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Quelle nicht gefunden")
    return await db.sources.find_one({"id": source_id}, {"_id": 0})


@api_router.delete("/sources/{source_id}")
async def delete_source(source_id: str, current_user: dict = Depends(require_admin)):
    """Delete source"""
    result = await db.sources.delete_one({"id": source_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Quelle nicht gefunden")
    return {"message": "Quelle gelöscht"}


# =============================================================================
# EVENT ROUTES
# =============================================================================

@api_router.post("/events", response_model=Event)
async def create_event(event_data: EventCreate, current_user: dict = Depends(get_current_user)):
    """Create new event"""
    event = Event(**event_data.model_dump())
    doc = serialize_datetime(event.model_dump())
    await db.events.insert_one(doc)
    return event


@api_router.get("/events", response_model=List[Event])
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None
):
    """Get all events"""
    query = {}
    if status:
        query["status"] = status
    events = await db.events.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return events


@api_router.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    """Get event by ID"""
    event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event nicht gefunden")
    return event


@api_router.put("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event_data: EventUpdate, current_user: dict = Depends(get_current_user)):
    """Update event"""
    update_data = {k: v for k, v in event_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.events.update_one({"id": event_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Event nicht gefunden")
    return await db.events.find_one({"id": event_id}, {"_id": 0})


@api_router.delete("/events/{event_id}")
async def delete_event(event_id: str, current_user: dict = Depends(require_admin)):
    """Delete event"""
    result = await db.events.delete_one({"id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event nicht gefunden")
    return {"message": "Event gelöscht"}


# =============================================================================
# TRANSFER ROUTES
# =============================================================================

@api_router.post("/transfers", response_model=Transfer)
async def create_transfer(transfer_data: TransferCreate, current_user: dict = Depends(get_current_user)):
    """Create new transfer"""
    transfer = Transfer(**transfer_data.model_dump())
    doc = serialize_datetime(transfer.model_dump())
    await db.transfers.insert_one(doc)
    return transfer


@api_router.get("/transfers", response_model=List[Transfer])
async def get_transfers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    player_id: Optional[str] = None,
    club_id: Optional[str] = None
):
    """Get all transfers"""
    query = {}
    if status:
        query["status"] = status
    if player_id:
        query["player_id"] = player_id
    if club_id:
        query["$or"] = [{"from_club_id": club_id}, {"to_club_id": club_id}]
    transfers = await db.transfers.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return transfers


@api_router.get("/transfers/confirmed", response_model=List[Transfer])
async def get_confirmed_transfers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get confirmed/official transfers"""
    query = {"status": {"$in": ["confirmed", "official"]}}
    transfers = await db.transfers.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return transfers


@api_router.get("/transfers/{transfer_id}", response_model=Transfer)
async def get_transfer(transfer_id: str):
    """Get transfer by ID"""
    transfer = await db.transfers.find_one({"id": transfer_id}, {"_id": 0})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer nicht gefunden")
    return transfer


@api_router.put("/transfers/{transfer_id}", response_model=Transfer)
async def update_transfer(transfer_id: str, transfer_data: TransferUpdate, current_user: dict = Depends(get_current_user)):
    """Update transfer"""
    update_data = {k: v for k, v in transfer_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.transfers.update_one({"id": transfer_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Transfer nicht gefunden")
    return await db.transfers.find_one({"id": transfer_id}, {"_id": 0})


@api_router.delete("/transfers/{transfer_id}")
async def delete_transfer(transfer_id: str, current_user: dict = Depends(require_admin)):
    """Delete transfer"""
    result = await db.transfers.delete_one({"id": transfer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transfer nicht gefunden")
    return {"message": "Transfer gelöscht"}


# =============================================================================
# RUMOUR ROUTES
# =============================================================================

@api_router.post("/rumours", response_model=Rumour)
async def create_rumour(rumour_data: RumourCreate, current_user: dict = Depends(get_current_user)):
    """Create new rumour"""
    rumour = Rumour(**rumour_data.model_dump())
    doc = serialize_datetime(rumour.model_dump())
    await db.rumours.insert_one(doc)
    return rumour


@api_router.get("/rumours", response_model=List[Rumour])
async def get_rumours(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    player_id: Optional[str] = None
):
    """Get all rumours"""
    query = {}
    if status:
        query["status"] = status
    if player_id:
        query["player_id"] = player_id
    rumours = await db.rumours.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return rumours


@api_router.get("/rumours/{rumour_id}", response_model=Rumour)
async def get_rumour(rumour_id: str):
    """Get rumour by ID"""
    rumour = await db.rumours.find_one({"id": rumour_id}, {"_id": 0})
    if not rumour:
        raise HTTPException(status_code=404, detail="Gerücht nicht gefunden")
    return rumour


@api_router.put("/rumours/{rumour_id}", response_model=Rumour)
async def update_rumour(rumour_id: str, rumour_data: RumourUpdate, current_user: dict = Depends(get_current_user)):
    """Update rumour"""
    update_data = {k: v for k, v in rumour_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.rumours.update_one({"id": rumour_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Gerücht nicht gefunden")
    return await db.rumours.find_one({"id": rumour_id}, {"_id": 0})


@api_router.delete("/rumours/{rumour_id}")
async def delete_rumour(rumour_id: str, current_user: dict = Depends(require_admin)):
    """Delete rumour"""
    result = await db.rumours.delete_one({"id": rumour_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Gerücht nicht gefunden")
    return {"message": "Gerücht gelöscht"}


# =============================================================================
# ARTICLE ROUTES
# =============================================================================

@api_router.post("/articles", response_model=Article)
async def create_article(article_data: ArticleCreate, current_user: dict = Depends(get_current_user)):
    """Create new article"""
    article = Article(**article_data.model_dump())
    doc = serialize_datetime(article.model_dump())
    await db.articles.insert_one(doc)
    return article


@api_router.get("/articles", response_model=List[Article])
async def get_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    article_type: Optional[str] = None,
    is_breaking: Optional[bool] = None,
    is_featured: Optional[bool] = None
):
    """Get all articles"""
    query = {}
    if status:
        query["status"] = status
    if article_type:
        query["article_type"] = article_type
    if is_breaking is not None:
        query["is_breaking"] = is_breaking
    if is_featured is not None:
        query["is_featured"] = is_featured
    articles = await db.articles.find(query, {"_id": 0}).sort("published_at", -1).skip(skip).limit(limit).to_list(limit)
    return articles


@api_router.get("/articles/published", response_model=List[Article])
async def get_published_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    article_type: Optional[str] = None
):
    """Get published articles for public display"""
    query = {"status": "published"}
    if article_type:
        query["article_type"] = article_type
    articles = await db.articles.find(query, {"_id": 0}).sort("published_at", -1).skip(skip).limit(limit).to_list(limit)
    return articles


@api_router.get("/articles/breaking", response_model=List[Article])
async def get_breaking_news(limit: int = Query(10, ge=1, le=20)):
    """Get breaking news for ticker"""
    query = {"status": "published", "is_breaking": True}
    articles = await db.articles.find(query, {"_id": 0}).sort("published_at", -1).limit(limit).to_list(limit)
    return articles


@api_router.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: str):
    """Get article by ID"""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
    return article


@api_router.get("/articles/slug/{slug}", response_model=Article)
async def get_article_by_slug(slug: str):
    """Get article by slug"""
    article = await db.articles.find_one({"slug": slug}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
    return article


@api_router.put("/articles/{article_id}", response_model=Article)
async def update_article(article_id: str, article_data: ArticleUpdate, current_user: dict = Depends(get_current_user)):
    """Update article"""
    update_data = {k: v for k, v in article_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    existing = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
    
    was_published = existing.get("status") == "published"
    
    # Auto-set published_at when publishing
    if article_data.status == ArticleStatus.PUBLISHED:
        if not existing.get("published_at"):
            update_data["published_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.articles.update_one({"id": article_id}, {"$set": update_data})
    
    # Auto-trigger pre-rendering when article is published
    if article_data.status == ArticleStatus.PUBLISHED:
        article_slug = existing.get("slug")
        if article_slug:
            # Trigger pre-rendering in background (don't block the response)
            asyncio.create_task(trigger_article_prerender(article_slug))
            logger.info(f"Pre-rendering triggered for: {article_slug}")
    
    return await db.articles.find_one({"id": article_id}, {"_id": 0})


@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str, current_user: dict = Depends(require_admin)):
    """Delete article"""
    result = await db.articles.delete_one({"id": article_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
    return {"message": "Artikel gelöscht"}


# Get articles by entity
@api_router.get("/articles/player/{player_id}", response_model=List[Article])
async def get_articles_by_player(player_id: str, limit: int = Query(10, ge=1, le=50)):
    """Get articles linked to a player"""
    query = {"status": "published", "linked_player_ids": player_id}
    articles = await db.articles.find(query, {"_id": 0}).sort("published_at", -1).limit(limit).to_list(limit)
    return articles


@api_router.get("/articles/club/{club_id}", response_model=List[Article])
async def get_articles_by_club(club_id: str, limit: int = Query(10, ge=1, le=50)):
    """Get articles linked to a club"""
    query = {"status": "published", "linked_club_ids": club_id}
    articles = await db.articles.find(query, {"_id": 0}).sort("published_at", -1).limit(limit).to_list(limit)
    return articles


@api_router.get("/articles/competition/{competition_id}", response_model=List[Article])
async def get_articles_by_competition(competition_id: str, limit: int = Query(10, ge=1, le=50)):
    """Get articles linked to a competition"""
    query = {"status": "published", "linked_competition_ids": competition_id}
    articles = await db.articles.find(query, {"_id": 0}).sort("published_at", -1).limit(limit).to_list(limit)
    return articles


# =============================================================================
# AD SLOT ROUTES
# =============================================================================

@api_router.post("/ad-slots", response_model=AdSlot)
async def create_ad_slot(slot_data: AdSlotCreate, current_user: dict = Depends(require_admin)):
    """Create new ad slot"""
    existing = await db.ad_slots.find_one({"slot_key": slot_data.slot_key})
    if existing:
        raise HTTPException(status_code=400, detail="Slot-Key bereits vorhanden")
    
    slot = AdSlot(**slot_data.model_dump())
    doc = serialize_datetime(slot.model_dump())
    await db.ad_slots.insert_one(doc)
    return slot


@api_router.get("/ad-slots", response_model=List[AdSlot])
async def get_ad_slots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    page_type: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """Get all ad slots"""
    query = {}
    if page_type:
        query["$or"] = [{"page_type": page_type}, {"page_type": "all"}]
    if is_active is not None:
        query["is_active"] = is_active
    slots = await db.ad_slots.find(query, {"_id": 0}).sort("priority", -1).skip(skip).limit(limit).to_list(limit)
    return slots


@api_router.get("/ad-slots/active", response_model=List[AdSlot])
async def get_active_ad_slots(
    page_type: Optional[str] = None,
    device_type: Optional[str] = None
):
    """Get active ad slots for rendering"""
    now = datetime.now(timezone.utc)
    query = {"is_active": True}
    
    if page_type:
        query["$or"] = [{"page_type": page_type}, {"page_type": "all"}]
    if device_type:
        query["$or"] = query.get("$or", []) + [{"device_type": device_type}, {"device_type": "all"}]
    
    slots = await db.ad_slots.find(query, {"_id": 0}).sort("priority", -1).to_list(200)
    
    # Filter by date range
    active_slots = []
    for slot in slots:
        start_date = slot.get("start_date")
        end_date = slot.get("end_date")
        
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            if now < start_date:
                continue
        
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            if now > end_date:
                continue
        
        active_slots.append(slot)
    
    return active_slots


@api_router.get("/ad-slots/{slot_id}", response_model=AdSlot)
async def get_ad_slot(slot_id: str):
    """Get ad slot by ID"""
    slot = await db.ad_slots.find_one({"id": slot_id}, {"_id": 0})
    if not slot:
        raise HTTPException(status_code=404, detail="Ad-Slot nicht gefunden")
    return slot


@api_router.get("/ad-slots/key/{slot_key}", response_model=AdSlot)
async def get_ad_slot_by_key(slot_key: str):
    """Get ad slot by key"""
    slot = await db.ad_slots.find_one({"slot_key": slot_key, "is_active": True}, {"_id": 0})
    if not slot:
        raise HTTPException(status_code=404, detail="Ad-Slot nicht gefunden")
    return slot


@api_router.put("/ad-slots/{slot_id}", response_model=AdSlot)
async def update_ad_slot(slot_id: str, slot_data: AdSlotUpdate, current_user: dict = Depends(require_admin)):
    """Update ad slot"""
    update_data = {k: v for k, v in slot_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.ad_slots.update_one({"id": slot_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ad-Slot nicht gefunden")
    return await db.ad_slots.find_one({"id": slot_id}, {"_id": 0})


@api_router.delete("/ad-slots/{slot_id}")
async def delete_ad_slot(slot_id: str, current_user: dict = Depends(require_admin)):
    """Delete ad slot"""
    result = await db.ad_slots.delete_one({"id": slot_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ad-Slot nicht gefunden")
    return {"message": "Ad-Slot gelöscht"}


# =============================================================================
# SETTINGS ROUTES
# =============================================================================

@api_router.get("/settings", response_model=List[Setting])
async def get_settings(current_user: dict = Depends(get_current_user)):
    """Get all settings"""
    settings = await db.settings.find({}, {"_id": 0}).to_list(100)
    return settings


@api_router.get("/settings/{key}")
async def get_setting(key: str):
    """Get setting by key"""
    setting = await db.settings.find_one({"key": key}, {"_id": 0})
    if not setting:
        raise HTTPException(status_code=404, detail="Einstellung nicht gefunden")
    return setting


@api_router.put("/settings/{key}", response_model=Setting)
async def update_setting(key: str, setting_data: SettingUpdate, current_user: dict = Depends(require_admin)):
    """Update or create setting"""
    existing = await db.settings.find_one({"key": key})
    
    if existing:
        update_data = {k: v for k, v in setting_data.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.settings.update_one({"key": key}, {"$set": update_data})
    else:
        setting = Setting(key=key, **setting_data.model_dump())
        doc = serialize_datetime(setting.model_dump())
        await db.settings.insert_one(doc)
    
    return await db.settings.find_one({"key": key}, {"_id": 0})


# =============================================================================
# SEARCH ROUTES
# =============================================================================

@api_router.get("/search")
async def search(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=50)
):
    """Global search across players, clubs, competitions, and articles"""
    results = {
        "players": [],
        "clubs": [],
        "competitions": [],
        "articles": []
    }
    
    search_regex = {"$regex": q, "$options": "i"}
    
    # Search players
    players = await db.players.find(
        {"$or": [{"name": search_regex}, {"aliases": search_regex}]},
        {"_id": 0, "id": 1, "name": 1, "slug": 1, "position": 1, "country": 1}
    ).limit(limit).to_list(limit)
    results["players"] = players
    
    # Search clubs
    clubs = await db.clubs.find(
        {"$or": [{"name": search_regex}, {"aliases": search_regex}]},
        {"_id": 0, "id": 1, "name": 1, "slug": 1, "country": 1}
    ).limit(limit).to_list(limit)
    results["clubs"] = clubs
    
    # Search competitions
    competitions = await db.competitions.find(
        {"name": search_regex},
        {"_id": 0, "id": 1, "name": 1, "slug": 1, "country": 1}
    ).limit(limit).to_list(limit)
    results["competitions"] = competitions
    
    # Search articles
    articles = await db.articles.find(
        {"status": "published", "$or": [{"title": search_regex}, {"excerpt": search_regex}]},
        {"_id": 0, "id": 1, "title": 1, "slug": 1, "excerpt": 1, "article_type": 1}
    ).limit(limit).to_list(limit)
    results["articles"] = articles
    
    return results


@api_router.get("/search/autosuggest")
async def autosuggest(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=20)
):
    """Quick autosuggest for search box"""
    suggestions = []
    search_regex = {"$regex": q, "$options": "i"}
    
    # Get players
    players = await db.players.find(
        {"$or": [{"name": search_regex}, {"aliases": search_regex}]},
        {"_id": 0, "id": 1, "name": 1, "slug": 1}
    ).limit(5).to_list(5)
    for p in players:
        suggestions.append({"type": "player", "id": p["id"], "name": p["name"], "slug": p["slug"]})
    
    # Get clubs
    clubs = await db.clubs.find(
        {"$or": [{"name": search_regex}, {"aliases": search_regex}]},
        {"_id": 0, "id": 1, "name": 1, "slug": 1}
    ).limit(5).to_list(5)
    for c in clubs:
        suggestions.append({"type": "club", "id": c["id"], "name": c["name"], "slug": c["slug"]})
    
    return suggestions[:limit]


# =============================================================================
# STATS / DASHBOARD
# =============================================================================

@api_router.get("/stats/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    stats = {
        "players": await db.players.count_documents({}),
        "clubs": await db.clubs.count_documents({}),
        "competitions": await db.competitions.count_documents({}),
        "sources": await db.sources.count_documents({}),
        "events_pending": await db.events.count_documents({"status": "pending"}),
        "events_total": await db.events.count_documents({}),
        "articles_draft": await db.articles.count_documents({"status": "draft"}),
        "articles_published": await db.articles.count_documents({"status": "published"}),
        "transfers_total": await db.transfers.count_documents({}),
        "rumours_active": await db.rumours.count_documents({"status": "active"}),
        "ad_slots_active": await db.ad_slots.count_documents({"is_active": True}),
        "ad_slots_total": await db.ad_slots.count_documents({})
    }
    return stats


# =============================================================================
# SEEDING / INITIALIZATION
# =============================================================================

@api_router.post("/init/admin")
async def init_admin():
    """Initialize default admin user if none exists"""
    admin_count = await db.users.count_documents({"role": "admin"})
    if admin_count > 0:
        return {"message": "Admin bereits vorhanden"}
    
    admin = User(
        email="admin@transfernews.de",
        name="Administrator",
        role=UserRole.ADMIN,
        password_hash=pwd_context.hash("admin123")
    )
    doc = serialize_datetime(admin.model_dump())
    await db.users.insert_one(doc)
    return {"message": "Admin erstellt", "email": "admin@transfernews.de", "password": "admin123"}


@api_router.post("/init/ad-slots")
async def init_ad_slots(current_user: dict = Depends(require_admin)):
    """Initialize default ad slots"""
    default_slots = [
        # Global slots
        {"name": "Top Banner Above Header", "slot_key": "top_banner_above_header", "page_type": "all", "position": "header_above", "device_type": "all"},
        {"name": "Header Inline", "slot_key": "header_inline", "page_type": "all", "position": "header_inline", "device_type": "all"},
        {"name": "Below Header", "slot_key": "below_header", "page_type": "all", "position": "header_below", "device_type": "all"},
        {"name": "Homepage Hero Banner", "slot_key": "homepage_hero_banner", "page_type": "homepage", "position": "hero", "device_type": "all"},
        {"name": "Homepage Feed Banner 1", "slot_key": "homepage_feed_banner_1", "page_type": "homepage", "position": "feed_1", "device_type": "all"},
        {"name": "Homepage Feed Banner 2", "slot_key": "homepage_feed_banner_2", "page_type": "homepage", "position": "feed_2", "device_type": "all"},
        {"name": "Homepage Feed Banner 3", "slot_key": "homepage_feed_banner_3", "page_type": "homepage", "position": "feed_3", "device_type": "all"},
        {"name": "Sidebar Top", "slot_key": "sidebar_top", "page_type": "all", "position": "sidebar_top", "device_type": "desktop"},
        {"name": "Sidebar Middle", "slot_key": "sidebar_middle", "page_type": "all", "position": "sidebar_middle", "device_type": "desktop"},
        {"name": "Sidebar Bottom", "slot_key": "sidebar_bottom", "page_type": "all", "position": "sidebar_bottom", "device_type": "desktop"},
        {"name": "Footer Top", "slot_key": "footer_top", "page_type": "all", "position": "footer_top", "device_type": "all"},
        {"name": "Footer Bottom", "slot_key": "footer_bottom", "page_type": "all", "position": "footer_bottom", "device_type": "all"},
        {"name": "Mobile Sticky Bottom", "slot_key": "mobile_sticky_bottom", "page_type": "all", "position": "sticky_bottom", "device_type": "mobile"},
        
        # Article slots
        {"name": "Article Below Title", "slot_key": "article_below_title", "page_type": "news_detail", "position": "below_title", "device_type": "all"},
        {"name": "Article Below Excerpt", "slot_key": "article_below_excerpt", "page_type": "news_detail", "position": "below_excerpt", "device_type": "all"},
        {"name": "Article After Paragraph 1", "slot_key": "article_after_paragraph_1", "page_type": "news_detail", "position": "after_p1", "device_type": "all"},
        {"name": "Article After Paragraph 2", "slot_key": "article_after_paragraph_2", "page_type": "news_detail", "position": "after_p2", "device_type": "all"},
        {"name": "Article After Paragraph 3", "slot_key": "article_after_paragraph_3", "page_type": "news_detail", "position": "after_p3", "device_type": "all"},
        {"name": "Article Before Related", "slot_key": "article_before_related", "page_type": "news_detail", "position": "before_related", "device_type": "all"},
        {"name": "Article After Related", "slot_key": "article_after_related", "page_type": "news_detail", "position": "after_related", "device_type": "all"},
        
        # Listing slots
        {"name": "Listing After Card 2", "slot_key": "listing_after_card_2", "page_type": "news_list", "position": "after_card_2", "device_type": "all", "feed_interval": 2},
        {"name": "Listing After Card 4", "slot_key": "listing_after_card_4", "page_type": "news_list", "position": "after_card_4", "device_type": "all", "feed_interval": 4},
        {"name": "Listing After Card 6", "slot_key": "listing_after_card_6", "page_type": "news_list", "position": "after_card_6", "device_type": "all", "feed_interval": 6},
        {"name": "Between Ticker and Feed", "slot_key": "between_ticker_and_feed", "page_type": "homepage", "position": "ticker_feed", "device_type": "all"},
        
        # Player page slots
        {"name": "Player Above Profile", "slot_key": "player_above_profile", "page_type": "player", "position": "above_profile", "device_type": "all"},
        {"name": "Player Below Profile", "slot_key": "player_below_profile", "page_type": "player", "position": "below_profile", "device_type": "all"},
        {"name": "Player Between News Blocks", "slot_key": "player_between_news_blocks", "page_type": "player", "position": "between_news", "device_type": "all"},
        
        # Club page slots
        {"name": "Club Above Header", "slot_key": "club_above_header", "page_type": "club", "position": "above_header", "device_type": "all"},
        {"name": "Club Below Header", "slot_key": "club_below_header", "page_type": "club", "position": "below_header", "device_type": "all"},
        {"name": "Club Between News Blocks", "slot_key": "club_between_news_blocks", "page_type": "club", "position": "between_news", "device_type": "all"},
        
        # Competition page slots
        {"name": "Competition Above Header", "slot_key": "competition_above_header", "page_type": "competition", "position": "above_header", "device_type": "all"},
        {"name": "Competition Below Header", "slot_key": "competition_below_header", "page_type": "competition", "position": "below_header", "device_type": "all"},
        
        # Search page slots
        {"name": "Search Results Top", "slot_key": "search_results_top", "page_type": "search", "position": "results_top", "device_type": "all"},
        {"name": "Search Results Between Items", "slot_key": "search_results_between_items", "page_type": "search", "position": "between_items", "device_type": "all", "feed_interval": 5},
    ]
    
    created = 0
    for slot_data in default_slots:
        existing = await db.ad_slots.find_one({"slot_key": slot_data["slot_key"]})
        if not existing:
            slot = AdSlot(**slot_data)
            doc = serialize_datetime(slot.model_dump())
            await db.ad_slots.insert_one(doc)
            created += 1
    
    return {"message": f"{created} Ad-Slots erstellt", "total": len(default_slots)}


# =============================================================================
# DATA IMPORT ROUTES
# =============================================================================

@api_router.post("/import/competition/{competition_code}")
async def import_competition(competition_code: str, current_user: dict = Depends(require_admin)):
    """
    Import competition, teams and players from football-data.org
    Codes: BL1 (Bundesliga), PL (Premier League), PD (La Liga), SA (Serie A), FL1 (Ligue 1), CL (Champions League)
    """
    from data_import import FootballDataAPI, import_competition_data
    
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="FOOTBALL_DATA_API_KEY nicht konfiguriert")
    
    api = FootballDataAPI(api_key)
    result = await import_competition_data(api, competition_code, db)
    
    return {
        "message": "Import abgeschlossen",
        "competition": result["competition"],
        "clubs_imported": result["clubs"],
        "players_imported": result["players"]
    }


@api_router.post("/import/scrape-news")
async def scrape_transfer_news(current_user: dict = Depends(require_admin)):
    """
    Scrape transfer news from RSS feeds (Sport1, Kicker, SPOX)
    """
    from data_import import import_rss_events
    
    result = await import_rss_events(db)
    
    return {
        "message": "RSS-Scraping abgeschlossen",
        "new_events": result["new_events"],
        "duplicates_skipped": result["duplicates"],
        "sources_created": result["sources_created"]
    }


@api_router.get("/import/available-competitions")
async def get_available_competitions():
    """Get list of available competition codes for import"""
    return {
        "competitions": [
            {"code": "BL1", "name": "Bundesliga", "country": "Germany"},
            {"code": "BL2", "name": "2. Bundesliga", "country": "Germany"},
            {"code": "PL", "name": "Premier League", "country": "England"},
            {"code": "PD", "name": "La Liga", "country": "Spain"},
            {"code": "SA", "name": "Serie A", "country": "Italy"},
            {"code": "FL1", "name": "Ligue 1", "country": "France"},
            {"code": "CL", "name": "Champions League", "country": "Europe"},
            {"code": "EL", "name": "Europa League", "country": "Europe"},
        ],
        "note": "Requires FOOTBALL_DATA_API_KEY in backend .env"
    }


@api_router.post("/import/generate-articles")
async def generate_articles_from_events(limit: int = 5, current_user: dict = Depends(require_admin)):
    """
    Generate articles from pending events using LLM
    """
    from data_import import process_pending_events
    
    result = await process_pending_events(db, limit=limit)
    
    return {
        "message": "Artikel-Generierung abgeschlossen",
        "events_processed": result["processed"],
        "articles_created": result["articles_created"],
        "errors": result["errors"]
    }


@api_router.post("/import/full-pipeline")
async def run_full_import_pipeline(current_user: dict = Depends(require_admin)):
    """
    Run full pipeline: Scrape RSS feeds -> Generate articles with LLM
    """
    from data_import import import_rss_events, process_pending_events
    
    # Step 1: Scrape RSS feeds
    scrape_result = await import_rss_events(db)
    
    # Step 2: Generate articles from new events
    gen_result = await process_pending_events(db, limit=10)
    
    return {
        "message": "Pipeline abgeschlossen",
        "scraping": {
            "new_events": scrape_result["new_events"],
            "duplicates_skipped": scrape_result["duplicates"]
        },
        "generation": {
            "articles_created": gen_result["articles_created"],
            "errors": gen_result["errors"]
        }
    }


@api_router.post("/import/refresh-images")
async def refresh_article_images(limit: int = Query(10, ge=1, le=50), current_user: dict = Depends(require_admin)):
    """
    Refresh images for existing articles by searching for player-related images
    """
    from data_import import find_best_player_image
    
    result = {"updated": 0, "errors": []}
    
    # Get articles with no or placeholder images
    articles = await db.articles.find(
        {"$or": [
            {"feature_image": {"$exists": False}},
            {"feature_image": ""},
            {"feature_image": {"$regex": "unsplash"}}
        ]},
        {"_id": 0}
    ).limit(limit).to_list(limit)
    
    for article in articles:
        try:
            new_image = await find_best_player_image(article.get("title", ""), article.get("id"))
            if new_image:
                await db.articles.update_one(
                    {"id": article["id"]},
                    {"$set": {"feature_image": new_image, "updated_at": datetime.now(timezone.utc).isoformat()}}
                )
                result["updated"] += 1
                logger.info(f"Updated image for: {article.get('title', '')[:40]}")
        except Exception as e:
            result["errors"].append(f"{article.get('id')}: {str(e)}")
            logger.error(f"Image refresh error: {e}")
    
    return {
        "message": f"{result['updated']} Artikel-Bilder aktualisiert",
        "updated": result["updated"],
        "errors": result["errors"]
    }


# =============================================================================
# HEALTH CHECK
# =============================================================================

@api_router.get("/")
async def root():
    return {"message": "TransferNews.de API", "version": "1.0.0"}


@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# =============================================================================
# TRENDING & BREAKING NEWS ROUTES
# =============================================================================

from trending import (
    calculate_event_score,
    get_trending_entities,
    get_trend_windows,
    get_breaking_news,
    get_player_landing_data,
    get_club_landing_data,
    get_competition_landing_data,
    get_theme_landing_data,
    get_free_transfers,
    get_top_transfers,
    generate_related_links,
    get_available_competitions,
    get_available_themes,
    batch_score_events
)


@api_router.get("/trending/players")
async def get_trending_players(hours: int = Query(24, ge=1, le=168)):
    """Get trending players based on recent event frequency"""
    result = await get_trending_entities(db, hours=hours)
    return {
        "trending_players": result["trending_players"],
        "period_hours": result["period_hours"]
    }


@api_router.get("/trending/clubs")
async def get_trending_clubs(hours: int = Query(24, ge=1, le=168)):
    """Get trending clubs based on recent event frequency"""
    result = await get_trending_entities(db, hours=hours)
    return {
        "trending_clubs": result["trending_clubs"],
        "period_hours": result["period_hours"]
    }


@api_router.get("/trending/all")
async def get_all_trending(hours: int = Query(24, ge=1, le=168)):
    """Get all trending entities (players + clubs)"""
    result = await get_trending_entities(db, hours=hours)
    return result


@api_router.get("/breaking")
async def get_breaking_articles(limit: int = Query(5, ge=1, le=20)):
    """Get latest breaking news articles"""
    articles = await get_breaking_news(db, limit=limit)
    return {"breaking_news": articles, "count": len(articles)}


@api_router.get("/landing/spieler/{slug}")
async def get_player_landing(slug: str):
    """Get all data for player SEO landing page"""
    data = await get_player_landing_data(db, slug)
    if not data:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    return data


@api_router.get("/landing/verein/{slug}")
async def get_club_landing(slug: str):
    """Get all data for club SEO landing page"""
    data = await get_club_landing_data(db, slug)
    if not data:
        raise HTTPException(status_code=404, detail="Verein nicht gefunden")
    return data


@api_router.get("/landing/abloesefreie")
async def get_free_transfer_articles():
    """Get articles about free transfers for SEO landing page"""
    articles = await get_free_transfers(db)
    return {
        "title": "Ablösefreie Transfers",
        "articles": articles,
        "count": len(articles)
    }


@api_router.get("/landing/top-transfers")
async def get_top_transfer_articles(limit: int = Query(20, ge=1, le=50)):
    """Get highest-probability transfer articles"""
    articles = await get_top_transfers(db, limit=limit)
    return {
        "title": "Top Transfers",
        "articles": articles,
        "count": len(articles)
    }


# =============================================================================
# COMPETITION & THEME LANDING PAGES (SEO)
# =============================================================================

@api_router.get("/wettbewerbe")
async def list_competitions():
    """List all available competitions for navigation"""
    return {"competitions": get_available_competitions()}


@api_router.get("/wettbewerb/{slug}")
async def get_competition_landing(slug: str):
    """Get all data for competition SEO landing page (e.g. /wettbewerb/bundesliga)"""
    data = await get_competition_landing_data(db, slug)
    if not data:
        raise HTTPException(status_code=404, detail="Wettbewerb nicht gefunden")
    return data


@api_router.get("/themen")
async def list_themes():
    """List all available themes for navigation"""
    return {"themes": get_available_themes()}


@api_router.get("/thema/{slug}")
async def get_theme_landing(slug: str):
    """Get all data for theme SEO landing page (e.g. /thema/abloesefreie-transfers)"""
    data = await get_theme_landing_data(db, slug)
    if not data:
        raise HTTPException(status_code=404, detail="Thema nicht gefunden")
    return data


# =============================================================================
# ENHANCED TRENDING WITH TIME WINDOWS
# =============================================================================

@api_router.get("/trending/windows")
async def get_trending_time_windows():
    """Get trending entities across multiple time windows (15min, 1h, 6h, 24h)"""
    return await get_trend_windows(db)


@api_router.get("/events/score")
async def score_recent_events(limit: int = Query(20, ge=1, le=100)):
    """Score recent events and return sorted by priority"""
    events = await db.events.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    scored_events = batch_score_events(events)
    
    return {
        "events": scored_events,
        "count": len(scored_events),
        "high_priority": len([e for e in scored_events if e["score_data"]["priority"] == "HIGH"]),
        "medium_priority": len([e for e in scored_events if e["score_data"]["priority"] == "MEDIUM"]),
        "low_priority": len([e for e in scored_events if e["score_data"]["priority"] == "LOW"])
    }


@api_router.get("/articles/{article_id}/related-links")
async def get_article_related_links(article_id: str):
    """Get internal links for article footer"""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
    
    links = generate_related_links(article)
    return {"article_id": article_id, "related_links": links}


@api_router.post("/events/{event_id}/calculate-score")
async def calculate_event_priority(event_id: str, current_user: dict = Depends(get_current_user)):
    """Calculate priority score for an event"""
    event = await db.events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Event nicht gefunden")
    
    score_result = calculate_event_score(event)
    
    # Update event with score
    await db.events.update_one(
        {"id": event_id},
        {"$set": {
            "priority_score": score_result["score"],
            "priority": score_result["priority"],
            "is_breaking": score_result["is_breaking"],
            "score_reasons": score_result["reasons"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return score_result


# =============================================================================
# PUBLIC NEWS ROUTES (Enhanced)
# =============================================================================

@api_router.get("/public/news")
async def get_public_news(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    status_filter: Optional[str] = None
):
    """Get published news for public display with optional status filter"""
    query = {"status": "published"}
    if status_filter:
        query["transfer_status"] = status_filter
    
    articles = await db.articles.find(query, {"_id": 0}).sort("published_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.articles.count_documents(query)
    
    return {
        "articles": articles,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@api_router.get("/public/news/{slug}")
async def get_public_news_detail(slug: str):
    """Get single news article with related links"""
    article = await db.articles.find_one({"slug": slug, "status": "published"}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
    
    # Add related links
    article["related_links"] = generate_related_links(article)
    
    return article


# =============================================================================
# SITEMAP & SEO ROUTES (Google News + Discover Optimization)
# =============================================================================

from fastapi.responses import Response
from sitemap import (
    generate_sitemap,
    generate_news_sitemap,
    generate_sitemap_index,
    generate_robots_txt,
    ping_google_sitemap,
    ping_google_news_sitemap,
    track_article_update
)


@api_router.get("/sitemap.xml", response_class=Response)
async def get_sitemap():
    """Standard sitemap for all pages"""
    content = await generate_sitemap(db)
    return Response(content=content, media_type="application/xml")


@api_router.get("/news-sitemap.xml", response_class=Response)
async def get_news_sitemap():
    """Google News sitemap - only articles from last 48 hours"""
    content = await generate_news_sitemap(db)
    return Response(content=content, media_type="application/xml")


@api_router.get("/sitemap-index.xml", response_class=Response)
async def get_sitemap_index():
    """Sitemap index pointing to all sitemaps"""
    content = await generate_sitemap_index()
    return Response(content=content, media_type="application/xml")


@api_router.get("/robots.txt", response_class=Response)
async def get_robots():
    """Optimized robots.txt for Google News"""
    content = generate_robots_txt()
    return Response(content=content, media_type="text/plain")


@api_router.post("/seo/ping-google")
async def trigger_google_ping(current_user: dict = Depends(get_current_user)):
    """Manually trigger Google sitemap ping"""
    sitemap_result = await ping_google_sitemap()
    news_result = await ping_google_news_sitemap()
    
    return {
        "sitemap_ping": sitemap_result,
        "news_sitemap_ping": news_result,
        "message": "Google wurde über Sitemap-Updates informiert" if sitemap_result else "Ping fehlgeschlagen"
    }


# =============================================================================
# ARTICLE UPDATE SYSTEM (Update statt Duplikate)
# =============================================================================

@api_router.post("/articles/{article_id}/update-status")
async def update_article_status(
    article_id: str,
    new_status: str = Query(..., description="New status: rumour, advanced, confirmed, official"),
    additional_info: str = Query(None, description="New information to append"),
    current_user: dict = Depends(get_current_user)
):
    """
    Update existing article status instead of creating duplicate
    Google loves updates, hates duplicate news
    """
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
    
    old_status = article.get("transfer_status", "rumour")
    now = datetime.now(timezone.utc).isoformat()
    
    # Build update
    update_data = {
        "transfer_status": new_status,
        "updated_at": now
    }
    
    # Append new information to body if provided
    if additional_info:
        current_body = article.get("body", "")
        
        # Create update paragraph
        status_labels = {
            "rumour": "Gerücht",
            "advanced": "Fortgeschritten", 
            "confirmed": "Bestätigt",
            "official": "Offiziell"
        }
        status_label = status_labels.get(new_status, new_status.upper())
        
        update_paragraph = f"\n\n**UPDATE ({status_label}):** {additional_info}"
        update_data["body"] = current_body + update_paragraph
    
    # Update probability based on status
    probability_map = {
        "rumour": 25,
        "advanced": 60,
        "confirmed": 85,
        "official": 100
    }
    if new_status in probability_map:
        update_data["transfer_probability"] = probability_map[new_status]
    
    # Perform update
    await db.articles.update_one(
        {"id": article_id},
        {"$set": update_data}
    )
    
    # Track the update
    await track_article_update(
        db, 
        article_id, 
        "status_change", 
        f"{old_status} → {new_status}"
    )
    
    # Ping Google about the update
    await ping_google_news_sitemap()
    
    return {
        "success": True,
        "article_id": article_id,
        "old_status": old_status,
        "new_status": new_status,
        "updated_at": now,
        "google_pinged": True
    }


@api_router.get("/check-duplicate-article")
async def check_for_duplicate_article(
    player_name: str = Query(...),
    club_name: str = Query(None),
    transfer_type: str = Query(None)
):
    """
    Check if an article about this transfer already exists
    Returns existing article if found, so it can be updated instead
    """
    # Find potential duplicates from last 7 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    
    # Build search query - search in title for player name
    # Note: published_at might be stored as datetime or string, handle both
    query = {
        "status": "published",
        "$or": [
            {"title": {"$regex": player_name, "$options": "i"}},
            {"body": {"$regex": player_name, "$options": "i"}}
        ]
    }
    
    # Get articles matching the player name
    all_matches = await db.articles.find(
        query,
        {"_id": 0, "id": 1, "title": 1, "slug": 1, "transfer_status": 1, "published_at": 1}
    ).sort("published_at", -1).limit(20).to_list(20)
    
    # Filter by date (handle both datetime and string formats)
    existing = []
    for article in all_matches:
        pub_date = article.get("published_at")
        if pub_date:
            # Handle datetime object
            if isinstance(pub_date, datetime):
                if pub_date.replace(tzinfo=timezone.utc) >= cutoff:
                    existing.append(article)
            # Handle string format
            elif isinstance(pub_date, str):
                try:
                    parsed = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                    if parsed >= cutoff:
                        existing.append(article)
                except:
                    existing.append(article)  # Include if we can't parse date
        
        if len(existing) >= 5:
            break
    
    # Serialize datetime objects for JSON response
    for article in existing:
        if isinstance(article.get("published_at"), datetime):
            article["published_at"] = article["published_at"].isoformat()
    
    return {
        "has_existing": len(existing) > 0,
        "existing_articles": existing,
        "recommendation": "update" if existing else "create_new"
    }


# =============================================================================
# AUTHOR PROFILE ROUTES (Trust Signals für Google News)
# =============================================================================

@api_router.post("/authors", response_model=Author)
async def create_author(author_data: AuthorCreate, current_user: dict = Depends(require_admin)):
    """Create new author profile"""
    existing = await db.authors.find_one({"slug": author_data.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Autor mit diesem Slug existiert bereits")
    
    author = Author(**author_data.model_dump())
    doc = serialize_datetime(author.model_dump())
    await db.authors.insert_one(doc)
    return author


@api_router.get("/authors", response_model=List[Author])
async def get_authors(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None
):
    """Get all authors"""
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    
    authors = await db.authors.find(query, {"_id": 0}).sort("name", 1).skip(skip).limit(limit).to_list(limit)
    return authors


@api_router.get("/authors/{slug}", response_model=Author)
async def get_author(slug: str):
    """Get author by slug"""
    author = await db.authors.find_one({"slug": slug}, {"_id": 0})
    if not author:
        raise HTTPException(status_code=404, detail="Autor nicht gefunden")
    return author


@api_router.put("/authors/{author_id}", response_model=Author)
async def update_author(author_id: str, author_data: AuthorUpdate, current_user: dict = Depends(require_admin)):
    """Update author profile"""
    update_dict = {k: v for k, v in author_data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="Keine Änderungen angegeben")
    
    update_dict["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.authors.update_one(
        {"id": author_id},
        {"$set": serialize_datetime(update_dict)}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Autor nicht gefunden")
    
    updated = await db.authors.find_one({"id": author_id}, {"_id": 0})
    return updated


@api_router.get("/authors/{slug}/articles")
async def get_author_articles(slug: str, limit: int = Query(20, ge=1, le=50)):
    """Get articles by author"""
    articles = await db.articles.find(
        {"author_slug": slug, "status": "published"},
        {"_id": 0}
    ).sort("published_at", -1).limit(limit).to_list(limit)
    
    return {"author_slug": slug, "articles": articles, "count": len(articles)}


@api_router.get("/public/authors/{slug}")
async def get_public_author(slug: str):
    """Get author profile with articles for public page"""
    author = await db.authors.find_one({"slug": slug, "is_active": True}, {"_id": 0})
    if not author:
        raise HTTPException(status_code=404, detail="Autor nicht gefunden")
    
    # Get author's articles
    articles = await db.articles.find(
        {"author_slug": slug, "status": "published"},
        {"_id": 0, "id": 1, "title": 1, "slug": 1, "excerpt": 1, "image_url": 1, "published_at": 1}
    ).sort("published_at", -1).limit(20).to_list(20)
    
    # Serialize datetime objects
    for article in articles:
        if isinstance(article.get("published_at"), datetime):
            article["published_at"] = article["published_at"].isoformat()
    
    return {
        **author,
        "articles": articles,
        "article_count": len(articles)
    }


# =============================================================================
# PRE-RENDERING & SCHEDULER ROUTES
# =============================================================================

from scheduler import (
    start_scheduler, stop_scheduler, get_scheduler_status,
    trigger_rss_scrape, trigger_event_processing, trigger_full_prerender
)
from prerender import (
    prerender_article, prerender_homepage, prerender_all_articles,
    get_prerendered_html, get_prerender_engine
)


@api_router.get("/scheduler/status")
async def get_scheduler_info(current_user: dict = Depends(get_current_user)):
    """Get scheduler status and job information"""
    return get_scheduler_status()


@api_router.post("/scheduler/start")
async def start_background_scheduler(current_user: dict = Depends(require_admin)):
    """Start the background scheduler"""
    start_scheduler()
    return {"status": "started", "jobs": get_scheduler_status()["jobs"]}


@api_router.post("/scheduler/stop")
async def stop_background_scheduler(current_user: dict = Depends(require_admin)):
    """Stop the background scheduler"""
    stop_scheduler()
    return {"status": "stopped"}


@api_router.post("/scheduler/trigger/rss")
async def manual_rss_scrape(current_user: dict = Depends(require_admin)):
    """Manually trigger RSS scrape"""
    result = await trigger_rss_scrape()
    return {"triggered": "rss_scrape", "result": result}


@api_router.post("/scheduler/trigger/events")
async def manual_event_processing(current_user: dict = Depends(require_admin)):
    """Manually trigger event processing"""
    result = await trigger_event_processing()
    return {"triggered": "event_processing", "result": result}


@api_router.post("/scheduler/trigger/prerender")
async def manual_prerender(current_user: dict = Depends(require_admin)):
    """Manually trigger full pre-render"""
    result = await trigger_full_prerender()
    return {"triggered": "prerender", "result": result}


@api_router.post("/prerender/article/{slug}")
async def prerender_single_article(slug: str, current_user: dict = Depends(get_current_user)):
    """Pre-render a single article"""
    success = await prerender_article(slug)
    return {"slug": slug, "success": success}


@api_router.post("/prerender/homepage")
async def prerender_home(current_user: dict = Depends(get_current_user)):
    """Pre-render homepage"""
    success = await prerender_homepage()
    return {"path": "/", "success": success}


@api_router.post("/prerender/all")
async def prerender_all(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_admin)
):
    """Pre-render all articles"""
    result = await prerender_all_articles(db, limit=limit)
    return result


@api_router.get("/prerender/status/{path:path}")
async def check_prerender_status(path: str):
    """Check if a path is pre-rendered"""
    full_path = f"/{path}" if not path.startswith("/") else path
    html = await get_prerendered_html(full_path)
    return {
        "path": full_path,
        "is_prerendered": html is not None,
        "html_length": len(html) if html else 0
    }


# =============================================================================
# CRAWLER HTML SERVING - Serve pre-rendered HTML to search engines
# =============================================================================

@api_router.get("/render/{path:path}", response_class=HTMLResponse)
async def serve_prerendered_html(path: str, request: Request):
    """
    Serve pre-rendered HTML for crawlers.
    This endpoint is called by nginx/ingress when a crawler is detected.
    
    Returns:
    - Pre-rendered HTML if available
    - 404 if not pre-rendered (frontend should handle this via SPA)
    """
    full_path = f"/{path}" if not path.startswith("/") else path
    
    # Check User-Agent
    user_agent = request.headers.get("user-agent", "")
    
    # Log crawler access
    if is_crawler(user_agent):
        logger.info(f"[CRAWLER] Serving pre-rendered HTML for: {full_path} (UA: {user_agent[:50]})")
    
    # Get pre-rendered HTML
    html = await get_prerendered_html(full_path)
    
    if html:
        return HTMLResponse(content=html, status_code=200)
    
    # No pre-rendered version available
    raise HTTPException(
        status_code=404, 
        detail=f"No pre-rendered content for {full_path}"
    )


@api_router.get("/ssr/{path:path}", response_class=HTMLResponse)
async def serve_ssr_html(path: str, request: Request):
    """
    Alternative endpoint for SSR/pre-rendered content.
    Can be used for testing or direct access to pre-rendered pages.
    """
    full_path = f"/{path}" if not path.startswith("/") else path
    html = await get_prerendered_html(full_path)
    
    if html:
        return HTMLResponse(content=html, status_code=200)
    
    # Fallback: try to pre-render on demand
    try:
        from prerender import PreRenderEngine, get_prerender_engine
        
        engine = await get_prerender_engine()
        html = await engine.render_page(full_path)
        
        if html:
            await engine.cache_html(full_path, html)
            logger.info(f"[SSR] On-demand rendered: {full_path}")
            return HTMLResponse(content=html, status_code=200)
    except Exception as e:
        logger.error(f"[SSR] On-demand render failed for {full_path}: {e}")
    
    raise HTTPException(
        status_code=404,
        detail=f"Could not render {full_path}"
    )


# =============================================================================
# GOOGLE SEARCH CONSOLE ROUTES
# =============================================================================

from search_console import get_gsc_service, GoogleSearchConsoleService


@api_router.get("/gsc/status")
async def get_gsc_status():
    """Check if Google Search Console is configured"""
    service = get_gsc_service()
    return {
        "configured": service.configured,
        "site_url": os.environ.get('SITE_URL', 'https://transfernews.de')
    }


@api_router.get("/gsc/dashboard")
async def get_gsc_dashboard(current_user: dict = Depends(get_current_user)):
    """Get complete GSC dashboard summary for Admin Panel"""
    service = get_gsc_service()
    return await service.get_dashboard_summary()


@api_router.post("/gsc/inspect-url")
async def inspect_url_indexation(
    url: str = Query(..., description="URL to inspect"),
    current_user: dict = Depends(get_current_user)
):
    """Inspect URL indexation status"""
    service = get_gsc_service()
    return await service.inspect_url(url)


@api_router.post("/gsc/inspect-batch")
async def inspect_urls_batch(
    urls: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Inspect multiple URLs"""
    service = get_gsc_service()
    return await service.batch_inspect_urls(urls)


@api_router.get("/gsc/performance")
async def get_search_performance(
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    dimensions: str = Query("date", description="Comma-separated dimensions"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get search performance data"""
    service = get_gsc_service()
    dimension_list = [d.strip() for d in dimensions.split(",")]
    return await service.get_performance_data(
        start_date=start_date,
        end_date=end_date,
        dimensions=dimension_list,
        row_limit=limit
    )


@api_router.get("/gsc/top-queries")
async def get_top_search_queries(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get top performing search queries"""
    service = get_gsc_service()
    return await service.get_top_queries(days=days, limit=limit)


@api_router.get("/gsc/top-pages")
async def get_top_performing_pages(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get top performing pages"""
    service = get_gsc_service()
    return await service.get_top_pages(days=days, limit=limit)


@api_router.get("/gsc/daily-stats")
async def get_daily_performance_stats(
    days: int = Query(30, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """Get daily performance stats for charts"""
    service = get_gsc_service()
    return await service.get_daily_stats(days=days)


@api_router.get("/gsc/device-breakdown")
async def get_device_performance(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """Get performance breakdown by device type"""
    service = get_gsc_service()
    return await service.get_device_breakdown(days=days)


@api_router.get("/gsc/country-breakdown")
async def get_country_performance(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Get performance breakdown by country"""
    service = get_gsc_service()
    return await service.get_country_breakdown(days=days, limit=limit)


@api_router.post("/gsc/submit-url")
async def submit_url_for_indexing(
    url: str = Query(..., description="URL to submit"),
    current_user: dict = Depends(get_current_user)
):
    """Submit a URL for indexing via Google Indexing API"""
    service = get_gsc_service()
    return await service.submit_url_for_indexing(url)


@api_router.post("/gsc/submit-batch")
async def submit_urls_batch(
    urls: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Submit multiple URLs for indexing"""
    service = get_gsc_service()
    return await service.submit_urls_batch(urls)


@api_router.post("/gsc/submit-all-articles")
async def submit_all_articles_for_indexing(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_admin)
):
    """Submit all published articles for indexing"""
    service = get_gsc_service()
    
    # Get published article URLs
    articles = await db.articles.find(
        {"status": "published"},
        {"_id": 0, "slug": 1}
    ).sort("published_at", -1).limit(limit).to_list(limit)
    
    site_url = os.environ.get('SITE_URL', 'https://transfernews.de')
    urls = [f"{site_url}/news/{article['slug']}" for article in articles if article.get('slug')]
    
    return await service.submit_urls_batch(urls)


# =============================================================================
# STARTUP - Auto-start scheduler
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Start scheduler on app startup"""
    try:
        start_scheduler()
        logger.info("Background scheduler started on startup")
        
        # Create default author if not exists
        default_author = await db.authors.find_one({"slug": "redaktion"})
        if not default_author:
            author = Author(
                name="Redaktion",
                slug="redaktion",
                bio="Die Redaktion von TransferNews.de berichtet täglich über aktuelle Transfers und Gerüchte aus der Welt des Fußballs.",
                expertise=["Bundesliga", "Premier League", "La Liga", "Champions League"],
                avatar_url="/api/static/images/author-redaktion.jpg"
            )
            await db.authors.insert_one(serialize_datetime(author.model_dump()))
            logger.info("Default author 'Redaktion' created")
            
    except Exception as e:
        logger.error(f"Startup error: {e}")


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
