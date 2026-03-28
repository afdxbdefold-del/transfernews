"""
TransferNews.de - Hauptserver
FastAPI Backend für die Fußball-Transfer-News-Plattform
"""

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import re

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
    DraftGenerationRequest, DraftGenerationResponse
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
    
    # Auto-set published_at when publishing
    if article_data.status == ArticleStatus.PUBLISHED:
        existing = await db.articles.find_one({"id": article_id}, {"_id": 0})
        if existing and not existing.get("published_at"):
            update_data["published_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.articles.update_one({"id": article_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
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
    get_breaking_news,
    get_player_landing_data,
    get_club_landing_data,
    get_free_transfers,
    get_top_transfers,
    generate_related_links
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
