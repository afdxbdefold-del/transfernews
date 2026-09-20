# TransferNews.de - Vollständige Technische Dokumentation

## Inhaltsverzeichnis

1. [Projektübersicht](#1-projektübersicht)
2. [Architektur](#2-architektur)
3. [Server-Infrastruktur](#3-server-infrastruktur)
4. [Backend](#4-backend)
5. [Frontend](#5-frontend)
6. [Datenbank](#6-datenbank)
7. [News-Pipeline](#7-news-pipeline)
8. [API-Referenz](#8-api-referenz)
9. [Deployment](#9-deployment)
10. [Troubleshooting](#10-troubleshooting)
11. [Bekannte Probleme](#11-bekannte-probleme)
12. [Wartung](#12-wartung)

---

## 1. Projektübersicht

### Was ist TransferNews.de?

Eine deutschsprachige Fußball-Transfer-News-Plattform, die automatisch Transfer-Gerüchte und offizielle Transfers aus RSS-Feeds scraped, mit GPT verbessert und veröffentlicht.

### Tech Stack

| Komponente | Technologie |
|------------|-------------|
| Frontend | React 18, TailwindCSS, Shadcn/UI |
| Backend | Python 3.11, FastAPI, Motor (async MongoDB) |
| Datenbank | MongoDB 7 |
| LLM | OpenAI GPT-4o-mini |
| Hosting | Hetzner VPS |
| Deployment | Coolify (selbst-gehostet) |
| Reverse Proxy | Nginx (manuell, ersetzt Coolify Traefik) |
| SSL | Let's Encrypt (Certbot) |

### Hauptfunktionen

- Automatisches RSS-Scraping von 20+ Quellen
- KI-gestützte Artikelgenerierung
- Spieler- und Vereinsseiten
- Admin-Dashboard
- Werbung (TheMonetizer, Primis)
- SEO-optimierte Sitemaps

---

## 2. Architektur

### Systemdiagramm

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTERNET                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     nginx-proxy (Port 80/443)                    │
│                                                                  │
│  /              → frontend:80                                    │
│  /api/          → backend:8001                                   │
│  /ads.txt       → /usr/share/nginx/html/ads.txt                 │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          ▼                                       ▼
┌─────────────────────┐               ┌─────────────────────┐
│     Frontend        │               │      Backend        │
│   (React, Port 80)  │               │ (FastAPI, Port 8001)│
│                     │               │                     │
│ - SPA               │               │ - REST API          │
│ - Routing           │               │ - Scheduler         │
│ - Ad Management     │               │ - News Pipeline     │
└─────────────────────┘               └──────────┬──────────┘
                                                 │
                                                 ▼
                                      ┌─────────────────────┐
                                      │      MongoDB        │
                                      │    (Port 27017)     │
                                      │                     │
                                      │ - articles          │
                                      │ - players           │
                                      │ - clubs             │
                                      │ - events            │
                                      │ - users             │
                                      └─────────────────────┘
```

### Docker-Container

| Container | Zweck | Port | Netzwerk |
|-----------|-------|------|----------|
| nginx-proxy | Reverse Proxy | 80, 443 | app-network |
| frontend-* | React App | 80 (intern) | app-network |
| backend-* | FastAPI | 8001 (intern) | app-network |
| mongodb-* | Datenbank | 27017 (intern) | app-network |

**WICHTIG:** Container-Namen von Coolify enthalten eine Deployment-ID, z.B. `backend-t4iysn7locgn8jdax7xb6s9j-222732202796`

---

## 3. Server-Infrastruktur

### Coolify vs Docker-Compose

Das Projekt verwendet **Coolify** für Deployment, NICHT docker-compose.

**KRITISCH:** Es existiert eine `docker-compose.yml` im Repository unter `/opt/transfernews/`. Diese darf NIEMALS verwendet werden, da sie eigene Container mit eigener MongoDB erstellt!

```bash
# FALSCH - erstellt Duplikate:
cd /opt/transfernews
docker compose up -d

# RICHTIG - nur Coolify-Container nutzen:
# Änderungen über Coolify Dashboard oder Git deployen
```

### Nginx Reverse Proxy

Coolify's Traefik wurde ersetzt wegen fehlerhafter Label-Generierung.

**Konfigurationspfad:** `/opt/nginx-proxy/nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:80;
    }
    
    upstream backend {
        server backend:8001;
    }

    server {
        listen 80;
        server_name transfernews.de www.transfernews.de;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name transfernews.de www.transfernews.de;

        ssl_certificate /etc/letsencrypt/live/transfernews.de/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/transfernews.de/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;

        location = /ads.txt {
            root /usr/share/nginx/html;
        }

        location /api/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### SSL-Zertifikate

- Pfad: `/etc/letsencrypt/live/transfernews.de/`
- Erneuerung: Automatisch via Certbot
- Gültigkeit prüfen: `certbot certificates`

---

## 4. Backend

### Verzeichnisstruktur

```
/app/backend/
├── server.py              # Haupt-FastAPI Server
├── models.py              # Pydantic Datenmodelle
├── scheduler.py           # APScheduler Cron-Jobs
├── speed_pipeline.py      # News-Verarbeitung
├── story_engine.py        # Story-Aggregation
├── data_import.py         # RSS-Import
├── entity_recognition.py  # Spieler/Verein-Erkennung
├── wikimedia_images.py    # Bildsuche
├── context_research.py    # Wikipedia-Kontext
├── trending.py            # Trending-Algorithmus
├── sitemap.py             # Sitemap-Generierung
├── prerender.py           # SEO Pre-Rendering
├── .env                   # Umgebungsvariablen
└── requirements.txt       # Python-Dependencies
```

### Wichtige Dateien

#### server.py
- FastAPI-Anwendung
- Alle API-Endpunkte
- Authentifizierung (JWT)
- Scheduler-Start

#### scheduler.py
- APScheduler-Konfiguration
- Cron-Jobs für:
  - RSS Scraping (2 Min)
  - Speed Pipeline (1 Min)
  - GPT Rewrite (5 Min)
  - Sitemap Update (2 Min)

#### speed_pipeline.py
- Verarbeitet Events zu Artikeln
- Template-basierte Sofort-Artikel
- GPT-Rewrite mit OpenAI
- "Unbekannt"-Filter (muss nach Redeploy wiederhergestellt werden!)

#### models.py
- Pydantic-Modelle für:
  - Player, Club, Competition
  - Article, Event, Transfer
  - User, AdSlot, Source

### Umgebungsvariablen

**Datei:** `/opt/transfernews/backend/.env`

```env
MONGO_URL=mongodb://mongodb:27017
DB_NAME=transfernews
# JWT_SECRET_FILE=/run/secrets/jwt_secret (serverseitig erzeugt; kein Standardwert)
# OPENAI_API_KEY wird ausschliesslich in Coolify hinterlegt.
```

### Scheduler-Jobs

| Job | Intervall | Funktion |
|-----|-----------|----------|
| RSS Feed Scraping | 2 Min | `task_rss_scrape()` |
| Speed Pipeline | 1 Min | `task_speed_pipeline()` |
| GPT Article Rewrite | 5 Min | `task_gpt_rewrite()` |
| News Sitemap Update | 2 Min | `task_update_sitemap()` |
| Internal Links | 3 Min | `task_internal_links()` |
| Pre-Rendering | 2 Std | `task_prerender()` |
| Cache Cleanup | 6 Std | `task_cache_cleanup()` |
| Health Check | 1 Min | `task_health_check()` |

---

## 5. Frontend

### Verzeichnisstruktur

```
/app/frontend/src/
├── App.js                 # Haupt-Router
├── api.js                 # API-Client (axios)
├── index.js               # Entry Point
├── pages/
│   ├── public/            # Öffentliche Seiten
│   │   ├── HomePage.jsx
│   │   ├── NewsDetailPage.jsx
│   │   ├── NewsListPage.jsx
│   │   ├── PlayerPage.jsx
│   │   ├── ClubPage.jsx
│   │   ├── CompetitionPage.jsx
│   │   ├── RumoursPage.jsx
│   │   ├── TransfersPage.jsx
│   │   ├── TickerPage.jsx
│   │   ├── TopDealsPage.jsx
│   │   ├── FreeAgentsPage.jsx
│   │   ├── DeadlineDayPage.jsx
│   │   ├── SearchPage.jsx
│   │   └── ...
│   └── admin/             # Admin-Bereich
│       ├── AdminDashboard.jsx
│       ├── AdminArticles.jsx
│       ├── AdminPlayers.jsx
│       ├── AdminClubs.jsx
│       ├── AdminAdSlots.jsx
│       └── ...
├── components/
│   ├── Header.jsx
│   ├── Footer.jsx
│   ├── TheMoneytizerAds.jsx
│   ├── DynamicAds.jsx
│   ├── StandardSidebar.jsx
│   └── ui/                # Shadcn Komponenten
└── styles/
```

### Routing (App.js)

```javascript
// Öffentliche Routen
/                    → HomePage
/news                → NewsListPage
/news/:slug          → NewsDetailPage
/spieler/:slug       → PlayerPage
/verein/:slug        → ClubPage
/wettbewerb/:slug    → CompetitionPage
/geruechte           → RumoursPage
/transfers           → TransfersPage
/ticker              → TickerPage
/top-deals           → TopDealsPage
/free-agents         → FreeAgentsPage
/deadline-day        → DeadlineDayPage
/suche               → SearchPage

// Admin Routen (geschützt)
/admin               → AdminDashboard
/admin/articles      → AdminArticles
/admin/players       → AdminPlayers
/admin/clubs         → AdminClubs
/admin/ad-slots      → AdminAdSlots
```

### API-Client (api.js)

```javascript
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { 'Content-Type': 'application/json' }
});

// Interceptor für Auth-Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const getArticles = (params) => api.get('/articles/published', { params });
export const getArticleBySlug = (slug) => api.get(`/articles/slug/${slug}`);
export const getPlayers = (params) => api.get('/players', { params });
export const getPlayerBySlug = (slug) => api.get(`/players/slug/${slug}`);
// ... weitere Exports
```

---

## 6. Datenbank

### Collections

#### articles
```javascript
{
  id: "uuid",
  title: "Spieler wechselt zu Verein",
  slug: "spieler-wechselt-zu-verein",
  body: "Artikeltext...",
  excerpt: "Kurzzusammenfassung",
  status: "published", // draft, review, published, archived
  article_type: "news", // rumour, transfer, analysis
  
  // Transfer-spezifisch
  player_id: "uuid",
  player_name: "Spielername",
  from_club_id: "uuid",
  to_club_id: "uuid",
  transfer_status: "rumour", // advanced, confirmed, official
  confidence_score: 75,
  
  // Medien
  image: "https://...",
  image_source: "Wikipedia",
  image_license: "CC BY-SA 4.0",
  
  // Autor
  author_id: "uuid",
  author_name: "Autorname",
  
  // SEO
  meta_title: "SEO Titel",
  meta_description: "SEO Beschreibung",
  
  // Flags
  is_breaking: false,
  is_featured: false,
  needs_gpt_rewrite: false,
  
  // Timestamps
  published_at: ISODate(),
  created_at: ISODate(),
  updated_at: ISODate()
}
```

#### players
```javascript
{
  id: "uuid",
  name: "Spielername",
  slug: "spielername",
  aliases: ["Spitzname", "Alter Name"],
  country: "Deutschland",
  birthdate: "1990-01-01",
  position: "Stürmer",
  current_club_id: "uuid",
  current_club_name: "FC Beispiel",
  market_value: 50000000,
  image: "https://...",
  created_at: ISODate(),
  updated_at: ISODate()
}
```

#### clubs
```javascript
{
  id: "uuid",
  name: "FC Beispiel",
  slug: "fc-beispiel",
  aliases: ["Beispiel FC"],
  country: "Deutschland",
  competition_id: "uuid",
  logo: "https://...",
  created_at: ISODate(),
  updated_at: ISODate()
}
```

#### events
```javascript
{
  id: "uuid",
  event_type: "rumour",
  status: "pending", // processed, rejected, published
  player_id: "uuid",
  from_club_id: "uuid",
  to_club_id: "uuid",
  headline_raw: "Originalüberschrift",
  body_raw: "Originaltext",
  source_url: "https://...",
  source_name: "Sky Sports",
  source_language: "en",
  confidence_score: 50,
  dedupe_key: "hash",
  created_at: ISODate()
}
```

#### users
```javascript
{
  id: "uuid",
  email: "admin@example.com",
  password_hash: "bcrypt_hash",
  name: "Admin",
  role: "admin", // editor, author
  is_active: true,
  created_at: ISODate()
}
```

#### ad_slots
```javascript
{
  id: "uuid",
  name: "Megabanner",
  slot_key: "megabanner",
  page_type: "all",
  position: "header_below",
  device_type: "desktop",
  embed_code: "<script>...</script>",
  is_active: true,
  priority: 100,
  created_at: ISODate()
}
```

### Indizes

```javascript
// articles
db.articles.createIndex({ "slug": 1 }, { unique: true })
db.articles.createIndex({ "status": 1, "published_at": -1 })
db.articles.createIndex({ "player_id": 1 })
db.articles.createIndex({ "dedupe_key": 1 })

// players
db.players.createIndex({ "slug": 1 }, { unique: true })
db.players.createIndex({ "name": "text", "aliases": "text" })

// events
db.events.createIndex({ "status": 1, "created_at": -1 })
db.events.createIndex({ "dedupe_key": 1 }, { unique: true })
```

---

## 7. News-Pipeline

### Übersicht

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  RSS Feeds   │────▶│    Events    │────▶│   Articles   │
│  (20+ Quellen)│     │  (pending)   │     │  (published) │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       │                    │                    │
       ▼                    ▼                    ▼
   data_import.py     speed_pipeline.py    GPT Rewrite
   (alle 2 Min)       (alle 1 Min)        (alle 5 Min)
```

### Phase 1: RSS Import

**Datei:** `data_import.py`
**Intervall:** Alle 2 Minuten

**Quellen:**
- Sky Sports, BBC Sport
- Marca, AS, Mundo Deportivo
- Gazzetta dello Sport, Corriere
- L'Équipe, RMC Sport, Foot Mercato
- kicker, BILD, Sport1
- CaughtOffside, TEAMtalk, 90min

**Ablauf:**
1. RSS-Feeds abrufen
2. Transfer-relevante Einträge filtern
3. Spieler/Verein erkennen
4. Dedupe-Key generieren
5. Als Event in DB speichern

### Phase 2: Speed Pipeline

**Datei:** `speed_pipeline.py`
**Intervall:** Alle 1 Minute

**Ablauf:**
1. Pending Events abrufen (max 20)
2. Story Engine: Events zu Stories aggregieren
3. Confidence Score berechnen
4. Template-basierten Sofort-Artikel generieren
5. Bild via Wikimedia suchen
6. Artikel speichern

**"Unbekannt"-Filter:**
```python
# In _create_article_from_story()
headline = story_result.get("headline", "")
if "nbekannt" in headline.lower():
    return None  # Artikel nicht erstellen
```

**WICHTIG:** Dieser Filter geht bei Coolify-Redeploy verloren!

### Phase 3: GPT Rewrite

**Datei:** `speed_pipeline.py` → `_gpt_rewrite_article()`
**Intervall:** Alle 5 Minuten

**Ablauf:**
1. Artikel mit `needs_gpt_rewrite=True` abrufen
2. Kontext aus Wikipedia laden
3. OpenAI GPT-4o-mini aufrufen
4. Artikel validieren (Länge, Qualität)
5. Artikel aktualisieren

**OpenAI-Aufruf:**
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

completion = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=2000
)
```

---

## 8. API-Referenz

### Authentifizierung

```
POST /api/auth/login
Body: { "email": "...", "password": "..." }
Response: { "access_token": "jwt...", "token_type": "bearer" }
```

Header für geschützte Routen:
```
Authorization: Bearer <token>
```

### Öffentliche Endpunkte

```
GET /api/articles/published?limit=50&skip=0
GET /api/articles/slug/{slug}
GET /api/articles/breaking?limit=10

GET /api/players?limit=50&search=...
GET /api/players/slug/{slug}
GET /api/players/{id}/transfers

GET /api/clubs?limit=50&search=...
GET /api/clubs/slug/{slug}

GET /api/competitions
GET /api/competitions/slug/{slug}

GET /api/trending/all?hours=24
GET /api/transfers/top-deals?limit=10

GET /api/health
GET /ads.txt
```

### Admin Endpunkte (Auth required)

```
POST /api/articles
PUT /api/articles/{id}
DELETE /api/articles/{id}

POST /api/players
PUT /api/players/{id}
DELETE /api/players/{id}

POST /api/clubs
PUT /api/clubs/{id}
DELETE /api/clubs/{id}

GET /api/ad-slots
POST /api/ad-slots
PUT /api/ad-slots/{id}
DELETE /api/ad-slots/{id}
GET /api/ad-slots/active

POST /api/init/ad-slots  # Initialisiert Standard-Slots
```

---

## 9. Deployment

### Nach Code-Änderungen

1. **In Emergent:** "Save to GitHub" klicken
2. **Auf Server:**
```bash
cd /opt/transfernews
git pull
# NICHT docker compose verwenden!
```
3. Coolify deployt automatisch (Webhook) oder manuell triggern
4. Nach Redeploy:
```bash
docker restart nginx-proxy
```
5. "Unbekannt"-Filter wiederherstellen (siehe unten)

### Filter nach Redeploy wiederherstellen

```bash
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)

docker exec $BACKEND sed -i '/async def _create_article_from_story/,/story = story_result.get("story", {})/{s/story = story_result.get("story", {})/story = story_result.get("story", {})\n        headline = story_result.get("headline", "")\n        if "nbekannt" in headline.lower():\n            return None/}' /app/speed_pipeline.py

docker restart $BACKEND
```

### Schnelle Änderungen im Container

```bash
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)

# Datei bearbeiten
docker exec -it $BACKEND vi /app/datei.py

# Container neustarten
docker restart $BACKEND
```

**Änderungen im Container gehen bei Redeploy verloren!**

---

## 10. Troubleshooting

### 502 Bad Gateway

```bash
# 1. Container-Status prüfen
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "backend|frontend|nginx|mongo"

# 2. Docker-compose Konflikte beseitigen
cd /opt/transfernews
docker compose down

# 3. Nginx neustarten
docker restart nginx-proxy

# 4. Backend-Logs prüfen
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)
docker logs --tail 50 $BACKEND
```

### Keine neuen News

```bash
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)

# Scheduler-Logs prüfen
docker logs --tail 30 $BACKEND | grep -E "(CRON|RSS|SPEED)"

# Events leeren (wenn alle Duplikate)
docker exec $BACKEND python3 -c '
from pymongo import MongoClient
import os
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
db.events.delete_many({})
print("Events geleert")
'

# OPENAI_API_KEY prüfen
docker exec $BACKEND printenv | grep OPENAI
```

### "Unbekannt"-Artikel löschen

```bash
docker exec $BACKEND python3 -c '
from pymongo import MongoClient
import os
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
r = db.articles.delete_many({"title": {"$regex": "nbekannt", "$options": "i"}})
print("Gelöscht:", r.deleted_count)
'
```

### Duplikate löschen

```bash
docker exec $BACKEND python3 -c '
from pymongo import MongoClient
import os
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
seen = {}
deleted = 0
for a in db.articles.find({"status": "published"}).sort("published_at", -1):
    title = a.get("title", "")
    if title in seen:
        db.articles.delete_one({"_id": a["_id"]})
        deleted += 1
    else:
        seen[title] = True
print("Duplikate gelöscht:", deleted)
'
```

### API zeigt alte Daten

```bash
# Prüfen ob zwei MongoDBs laufen
docker ps | grep mongo

# Wenn transfernews-mongodb-1 läuft:
cd /opt/transfernews
docker compose down

# Nginx DNS aktualisieren
docker restart nginx-proxy
```

---

## 11. Bekannte Probleme

### 1. Coolify Traefik-Labels fehlerhaft
**Problem:** Coolify generiert `Host(``) && PathPrefix(`transfernews.de`)` statt `Host(`transfernews.de`)`
**Lösung:** Eigener Nginx-Proxy

### 2. Container-Namen ändern sich bei Redeploy
**Problem:** Coolify generiert neue Container-IDs
**Lösung:** Container immer dynamisch ermitteln:
```bash
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)
```

### 3. Docker-compose und Coolify Konflikt
**Problem:** docker-compose erstellt eigene Container mit eigener MongoDB
**Lösung:** NIEMALS `docker compose up` verwenden

### 4. "Unbekannt"-Filter geht verloren
**Problem:** Filter wird bei Redeploy überschrieben
**Lösung:** Nach jedem Redeploy manuell wiederherstellen

### 5. RSS Events werden zu Duplikaten
**Problem:** Alle Events als "duplicate" erkannt
**Lösung:** Events-Collection leeren

### 6. OpenAI-Key fehlt nach Redeploy
**Problem:** Environment-Variable nicht gesetzt
**Lösung:** In Coolify Dashboard unter Environment Variables prüfen

---

## 12. Wartung

### Tägliche Checks

```bash
# Container-Status
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "backend|frontend|mongo"

# Letzte Artikel
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)
docker exec $BACKEND python3 -c '
from pymongo import MongoClient
import os
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
for a in db.articles.find({"status": "published"}).sort("published_at", -1).limit(5):
    print(a.get("published_at", "")[:16], a.get("title", "")[:50])
'

# Scheduler-Logs
docker logs --tail 20 $BACKEND | grep CRON
```

### Wöchentliche Wartung

```bash
# Alte Draft-Artikel löschen
docker exec $BACKEND python3 -c '
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import os
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
cutoff = datetime.now(timezone.utc) - timedelta(days=7)
r = db.articles.delete_many({"status": "draft", "created_at": {"$lt": cutoff}})
print("Alte Drafts gelöscht:", r.deleted_count)
'

# Alte Events löschen
docker exec $BACKEND python3 -c '
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import os
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
cutoff = datetime.now(timezone.utc) - timedelta(days=3)
r = db.events.delete_many({"created_at": {"$lt": cutoff}})
print("Alte Events gelöscht:", r.deleted_count)
'

# Docker Cleanup
docker system prune -f
```

### SSL-Zertifikat erneuern

```bash
# Prüfen
certbot certificates

# Manuell erneuern (falls nötig)
certbot renew

# Nginx neu laden
docker exec nginx-proxy nginx -s reload
```

---

## Wichtige Befehle Zusammenfassung

```bash
# Backend Container ermitteln
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)

# Container-Status
docker ps | grep -E "backend|frontend|mongo|nginx"

# Logs
docker logs --tail 50 $BACKEND

# Nginx neustarten
docker restart nginx-proxy

# Backend neustarten
docker restart $BACKEND

# API testen
curl -s "https://transfernews.de/api/health"
curl -s "https://transfernews.de/api/articles/published?limit=3"

# MongoDB-Operationen
docker exec $BACKEND python3 -c 'CODE_HIER'

# Docker-compose stoppen (falls versehentlich gestartet)
cd /opt/transfernews && docker compose down
```

---

## Kontakt

Bei Problemen:
1. Diese Dokumentation durchgehen
2. Logs prüfen
3. Bekannte Probleme durchgehen
4. Container-Status verifizieren
