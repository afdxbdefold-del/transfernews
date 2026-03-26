"""
TransferNews.de - Datenmodelle
Vollständiges relationales Datenmodell für die Transfer-News-Plattform
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


def generate_uuid():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


# =============================================================================
# ENUMS
# =============================================================================

class EntityType(str, Enum):
    PLAYER = "player"
    CLUB = "club"
    COMPETITION = "competition"


class EventType(str, Enum):
    RUMOUR = "rumour"
    ADVANCED = "advanced"
    CONFIRMED = "confirmed"
    OFFICIAL = "official"


class EventStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    REJECTED = "rejected"
    PUBLISHED = "published"


class TransferType(str, Enum):
    PERMANENT = "permanent"
    LOAN = "loan"
    FREE = "free"
    LOAN_WITH_OPTION = "loan_with_option"
    YOUTH = "youth"


class TransferStatus(str, Enum):
    RUMOUR = "rumour"
    ADVANCED = "advanced"
    CONFIRMED = "confirmed"
    OFFICIAL = "official"


class RumourStatus(str, Enum):
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    DENIED = "denied"
    EXPIRED = "expired"


class ArticleType(str, Enum):
    NEWS = "news"
    RUMOUR = "rumour"
    TRANSFER = "transfer"
    ANALYSIS = "analysis"
    INTERVIEW = "interview"
    SPECIAL = "special"


class ArticleStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SourceType(str, Enum):
    OFFICIAL = "official"
    JOURNALIST = "journalist"
    MEDIA = "media"
    AGGREGATOR = "aggregator"
    SOCIAL = "social"


class SourceCategory(str, Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"
    UNVERIFIED = "unverified"


class DeviceType(str, Enum):
    ALL = "all"
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"


class PageType(str, Enum):
    ALL = "all"
    HOMEPAGE = "homepage"
    NEWS_LIST = "news_list"
    NEWS_DETAIL = "news_detail"
    PLAYER = "player"
    CLUB = "club"
    COMPETITION = "competition"
    RUMOURS = "rumours"
    TRANSFERS = "transfers"
    SEARCH = "search"
    TOPIC = "topic"


class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    AUTHOR = "author"


# =============================================================================
# BASE MODELS
# =============================================================================

class BaseMongoModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True
    )


# =============================================================================
# PLAYERS
# =============================================================================

class PlayerBase(BaseModel):
    name: str
    slug: str
    aliases: List[str] = []
    country: Optional[str] = None
    birthdate: Optional[str] = None
    position: Optional[str] = None
    current_club_id: Optional[str] = None
    image: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class PlayerCreate(PlayerBase):
    pass


class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    aliases: Optional[List[str]] = None
    country: Optional[str] = None
    birthdate: Optional[str] = None
    position: Optional[str] = None
    current_club_id: Optional[str] = None
    image: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class Player(PlayerBase, BaseMongoModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# CLUBS
# =============================================================================

class ClubBase(BaseModel):
    name: str
    slug: str
    aliases: List[str] = []
    country: Optional[str] = None
    competition_id: Optional[str] = None
    logo: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ClubCreate(ClubBase):
    pass


class ClubUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    aliases: Optional[List[str]] = None
    country: Optional[str] = None
    competition_id: Optional[str] = None
    logo: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class Club(ClubBase, BaseMongoModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# COMPETITIONS
# =============================================================================

class CompetitionBase(BaseModel):
    name: str
    slug: str
    country: Optional[str] = None
    type: str = "league"
    logo: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class CompetitionCreate(CompetitionBase):
    pass


class CompetitionUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    country: Optional[str] = None
    type: Optional[str] = None
    logo: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class Competition(CompetitionBase, BaseMongoModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# SOURCES
# =============================================================================

class SourceBase(BaseModel):
    name: str
    slug: str
    type: SourceType = SourceType.MEDIA
    source_url: Optional[str] = None
    source_category: SourceCategory = SourceCategory.TIER_2
    active: bool = True
    trust_score: Optional[int] = Field(default=50, ge=0, le=100)


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    type: Optional[SourceType] = None
    source_url: Optional[str] = None
    source_category: Optional[SourceCategory] = None
    active: Optional[bool] = None
    trust_score: Optional[int] = None


class Source(SourceBase, BaseMongoModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# EVENTS (Raw Input from Scrapers)
# =============================================================================

class EventBase(BaseModel):
    event_type: EventType = EventType.RUMOUR
    status: EventStatus = EventStatus.PENDING
    player_id: Optional[str] = None
    from_club_id: Optional[str] = None
    to_club_id: Optional[str] = None
    competition_id: Optional[str] = None
    headline_raw: str
    body_raw: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    source_published_at: Optional[datetime] = None
    confidence_score: Optional[int] = Field(default=50, ge=0, le=100)
    dedupe_key: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    event_type: Optional[EventType] = None
    status: Optional[EventStatus] = None
    player_id: Optional[str] = None
    from_club_id: Optional[str] = None
    to_club_id: Optional[str] = None
    competition_id: Optional[str] = None
    headline_raw: Optional[str] = None
    body_raw: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    source_published_at: Optional[datetime] = None
    confidence_score: Optional[int] = None
    dedupe_key: Optional[str] = None


class Event(EventBase, BaseMongoModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# TRANSFERS
# =============================================================================

class TransferBase(BaseModel):
    player_id: str
    from_club_id: Optional[str] = None
    to_club_id: Optional[str] = None
    transfer_type: TransferType = TransferType.PERMANENT
    fee_amount: Optional[float] = None
    fee_currency: str = "EUR"
    season: Optional[str] = None
    status: TransferStatus = TransferStatus.RUMOUR
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    announced_at: Optional[datetime] = None


class TransferCreate(TransferBase):
    pass


class TransferUpdate(BaseModel):
    player_id: Optional[str] = None
    from_club_id: Optional[str] = None
    to_club_id: Optional[str] = None
    transfer_type: Optional[TransferType] = None
    fee_amount: Optional[float] = None
    fee_currency: Optional[str] = None
    season: Optional[str] = None
    status: Optional[TransferStatus] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    announced_at: Optional[datetime] = None


class Transfer(TransferBase, BaseMongoModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# RUMOURS
# =============================================================================

class RumourBase(BaseModel):
    player_id: str
    target_club_id: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    confidence_score: int = Field(default=50, ge=0, le=100)
    status: RumourStatus = RumourStatus.ACTIVE


class RumourCreate(RumourBase):
    pass


class RumourUpdate(BaseModel):
    player_id: Optional[str] = None
    target_club_id: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    confidence_score: Optional[int] = None
    status: Optional[RumourStatus] = None


class Rumour(RumourBase, BaseMongoModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# ARTICLES
# =============================================================================

class ArticleBase(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    body: Optional[str] = None
    article_type: ArticleType = ArticleType.NEWS
    status: ArticleStatus = ArticleStatus.DRAFT
    published_at: Optional[datetime] = None
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None
    social_title: Optional[str] = None
    social_description: Optional[str] = None
    feature_image: Optional[str] = None
    linked_player_ids: List[str] = []
    linked_club_ids: List[str] = []
    linked_competition_ids: List[str] = []
    linked_source_ids: List[str] = []
    linked_event_id: Optional[str] = None
    is_breaking: bool = False
    is_featured: bool = False


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    body: Optional[str] = None
    article_type: Optional[ArticleType] = None
    status: Optional[ArticleStatus] = None
    published_at: Optional[datetime] = None
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None
    social_title: Optional[str] = None
    social_description: Optional[str] = None
    feature_image: Optional[str] = None
    linked_player_ids: Optional[List[str]] = None
    linked_club_ids: Optional[List[str]] = None
    linked_competition_ids: Optional[List[str]] = None
    linked_source_ids: Optional[List[str]] = None
    linked_event_id: Optional[str] = None
    is_breaking: Optional[bool] = None
    is_featured: Optional[bool] = None


class Article(ArticleBase, BaseMongoModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# ALIASES (for entity recognition)
# =============================================================================

class AliasBase(BaseModel):
    entity_type: EntityType
    entity_id: str
    alias: str
    normalized_alias: str


class AliasCreate(AliasBase):
    pass


class Alias(AliasBase, BaseMongoModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# AD SLOTS
# =============================================================================

class AdSlotBase(BaseModel):
    name: str
    slot_key: str
    page_type: PageType = PageType.ALL
    position: str
    device_type: DeviceType = DeviceType.ALL
    html_code: Optional[str] = None
    js_code: Optional[str] = None
    embed_code: Optional[str] = None
    is_active: bool = True
    priority: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None
    feed_interval: Optional[int] = None  # For feed ads: show after every N items


class AdSlotCreate(AdSlotBase):
    pass


class AdSlotUpdate(BaseModel):
    name: Optional[str] = None
    slot_key: Optional[str] = None
    page_type: Optional[PageType] = None
    position: Optional[str] = None
    device_type: Optional[DeviceType] = None
    html_code: Optional[str] = None
    js_code: Optional[str] = None
    embed_code: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None
    feed_interval: Optional[int] = None


class AdSlot(AdSlotBase, BaseMongoModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# USERS (Admin)
# =============================================================================

class UserBase(BaseModel):
    email: str
    name: str
    role: UserRole = UserRole.AUTHOR


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None


class User(UserBase, BaseMongoModel):
    id: str = Field(default_factory=generate_uuid)
    password_hash: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class UserPublic(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    is_active: bool


# =============================================================================
# SETTINGS
# =============================================================================

class SettingBase(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None


class SettingCreate(SettingBase):
    pass


class SettingUpdate(BaseModel):
    value: Optional[Any] = None
    description: Optional[str] = None


class Setting(SettingBase, BaseMongoModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# API RESPONSES
# =============================================================================

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


# =============================================================================
# LLM / Draft Generation
# =============================================================================

class DraftGenerationRequest(BaseModel):
    event_id: str
    generate_headline: bool = True
    generate_excerpt: bool = True
    generate_body: bool = True
    generate_seo: bool = True


class DraftGenerationResponse(BaseModel):
    title: Optional[str] = None
    excerpt: Optional[str] = None
    body: Optional[str] = None
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    success: bool
    message: Optional[str] = None
