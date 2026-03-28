# TransferNews.de - Product Requirements Document

## Original Problem Statement
Deutschsprachige Fußball-Transfer-News-Plattform auf der Domain transfernews.de mit:
- Transfer-News, Gerüchte, bestätigte Transfers, offizielle Wechsel
- Spielerseiten, Vereinsseiten, Wettbewerbsseiten
- Automatische News-Generierung aus strukturierten Rohdaten
- LLM-basierte Multi-Source Artikel-Generierung
- **Layout: Pixel-perfekte Kopie von sport1.de**
- **Content: Streng limitiert auf Fußball-Transfers**
- **SEO: Google Discover + Google News optimiert**
- **NEU: GOOGLE NEWS DOMINANCE SYSTEM**

## Technical Architecture
- **Frontend:** React 19 mit Tailwind CSS, Shadcn UI, Phosphor Icons, react-helmet-async
- **Backend:** FastAPI (Python)
- **Datenbank:** MongoDB
- **Auth:** JWT-basiertes Admin-Login
- **LLM:** emergentintegrations (GPT-4o via Emergent LLM Key)
- **RSS:** feedparser für 6 deutsche Nachrichtenquellen
- **Bilder:** aiohttp für Downloads, Unsplash/Pexels für Stadionbilder

## What's Been Implemented

### 28. März 2026 - GOOGLE SEARCH CONSOLE ADMIN DASHBOARD
- ✅ **GSC Service** (`/app/backend/search_console.py`) - Vollständiger Service für GSC API Integration
- ✅ **URL Inspection API** - Indexierungsstatus einzelner URLs prüfen
- ✅ **Search Analytics API** - Klicks, Impressionen, CTR, Position abrufen
- ✅ **Indexing API** - URLs zur Indexierung einreichen
- ✅ **Admin Dashboard** (`/admin/gsc`) - Vollständiges GSC Dashboard im Admin-Panel
- ✅ **Setup-Anleitung** - Zeigt Schritt-für-Schritt Anleitung wenn nicht konfiguriert
- ✅ **API Endpoints**:
  - `GET /api/gsc/status` - Konfigurationsstatus
  - `GET /api/gsc/dashboard` - Dashboard Summary
  - `POST /api/gsc/inspect-url` - URL prüfen
  - `GET /api/gsc/performance` - Performance-Daten
  - `POST /api/gsc/submit-url` - URL einreichen
  - `POST /api/gsc/submit-all-articles` - Alle Artikel einreichen

### 28. März 2026 - PRE-RENDERING & CRAWLER-SERVING
- ✅ **Playwright Pre-Rendering** (`/app/backend/prerender.py`) - Rendert React-Seiten zu statischem HTML
- ✅ **Crawler-Detection** - User-Agent Prüfung für GoogleBot, BingBot, etc.
- ✅ **Pre-Render Serving** (`/api/render/{path}`) - Liefert statisches HTML an Crawler
- ✅ **SSR Endpoint** (`/api/ssr/{path}`) - On-Demand Rendering wenn Cache leer
- ✅ **Auto-Trigger nach Publish** - Artikel werden automatisch pre-rendered nach Veröffentlichung
- ✅ **APScheduler Cronjobs** (`/app/backend/scheduler.py`):
  - RSS Scraping alle 30 Minuten
  - Event-Processing alle 30 Minuten
  - Full Pre-Render alle 12 Stunden
  - Cache Cleanup alle 6 Stunden
  - Google Ping alle 60 Minuten
- ✅ **Autor-Profile** (`/api/public/authors/{slug}`) mit Frontend-Seite

### 28. März 2026 - GOOGLE NEWS + DISCOVER DOMINANCE SYSTEM
- ✅ **XML Sitemap** (`/api/sitemap.xml`) - Alle Seiten mit lastmod, changefreq, priority
- ✅ **News Sitemap** (`/api/news-sitemap.xml`) - Nur Artikel der letzten 48h für Google News
- ✅ **Sitemap Index** (`/api/sitemap-index.xml`) - Verweist auf alle Sitemaps
- ✅ **robots.txt** (`/api/robots.txt`) - Optimiert für Google News/Discover
- ✅ **Google Ping** - Automatisches Pingen von Google bei neuen Artikeln
- ✅ **Update statt Duplikate** - Bestehende Artikel werden aktualisiert statt neue erstellt
- ✅ **Check Duplicate API** (`/api/check-duplicate-article`) - Prüft ob Artikel existiert
- ✅ **Update Status API** (`/api/articles/{id}/update-status`) - Status-Updates mit Textanhang
- ✅ **Article Update Tracker** - Protokolliert alle Updates für Transparenz

### 28. März 2026 - TREND + BREAKING + SEO System
- ✅ API-Endpoints für Trending/Breaking/Landing-Pages
- ✅ TrendingWidget Komponente für Sidebar
- ✅ TrendingBar horizontale Komponente
- ✅ RelatedLinks für automatische interne Verlinkung
- ✅ Schema.org JSON-LD für Person, SportsTeam, WebSite, NewsArticle

### März 2026 - Content Pipeline & SEO
- ✅ RSS Feed Scraper (6 deutsche Quellen)
- ✅ Strenge Transfer-Keywords-Filterung
- ✅ Multi-Source LLM Artikel-Generierung
- ✅ Lokale Bildspeicherung
- ✅ react-helmet-async SEO Integration

### März 2026 - Sport1.de Layout Redesign
- ✅ Kompletter Frontend-Umbau im sport1.de-Stil
- ✅ Neuer zweistufiger Header
- ✅ Newsticker-Komponenten mit Zeit-Badges
- ✅ Hero-Teaser mit Gradient-Overlay
- ✅ Breaking News Ticker
- ✅ Status-Badges (GERÜCHT, OFFIZIELL, BESTÄTIGT)
- ✅ Transfer-Wahrscheinlichkeits-Balken

## Key API Endpoints

### SEO & Sitemaps
- `GET /api/sitemap.xml` - Standard XML Sitemap
- `GET /api/news-sitemap.xml` - Google News Sitemap (48h)
- `GET /api/sitemap-index.xml` - Sitemap Index
- `GET /api/robots.txt` - Robots.txt für Crawler
- `POST /api/seo/ping-google` - Manueller Google Ping (Admin)

### Article Updates (KRITISCH für Google News)
- `GET /api/check-duplicate-article?player_name=...` - Prüft ob Artikel existiert
- `POST /api/articles/{id}/update-status?new_status=...&additional_info=...` - Status updaten

### Trending & Breaking
- `GET /api/trending/all` - Trending Spieler & Vereine
- `GET /api/breaking` - Breaking News
- `GET /api/landing/spieler/{slug}` - Spieler-Landingpage
- `GET /api/landing/verein/{slug}` - Vereins-Landingpage

## Prioritized Backlog

### P0 (Completed)
- [x] MVP komplett implementiert
- [x] Sport1.de-Style Layout
- [x] RSS Scraper & LLM Pipeline
- [x] Google Discover SEO Tags
- [x] TREND + BREAKING System
- [x] **GOOGLE NEWS DOMINANCE SYSTEM**
- [x] **PRE-RENDERING SYSTEM** (Playwright-basiert, mit Auto-Trigger nach Publish)
- [x] **CRONJOB SYSTEM** (APScheduler: RSS 30min, Events 30min, Prerender 12h, Google Ping 1h)
- [x] **AUTOR-PROFILE** (AuthorPage.jsx mit Artikel-Liste)
- [x] **CRAWLER-SERVING** (Pre-Rendered HTML für GoogleBot & Co.)

### P1 (Nächste Phase)
- [ ] Breaking-Engine Score-Berechnung (Event-Scoring nach Quelle, Spieler-Level, Club-Level)
- [ ] Trend-System Zeitfenster-Logik (15m, 1h, 6h, 24h Cluster für trend_score)
- [ ] SEO-Landingpages dynamische Routen (`/wettbewerb/{slug}`, `/thema/...`)
- [ ] Homepage als Live-Feed (Auto-Refresh alle 60s)

### P2 (Später)
- [ ] Themenseiten (Deadline Day, Sommertransfers, etc.)
- [ ] Newsletter-Integration
- [ ] Performance-Optimierung (Redis Caching)

## Admin Credentials
- Email: admin@transfernews.de
- Password: admin123

## Key Files

### Backend
- `/app/backend/server.py` - API Endpoints inkl. SEO/Sitemaps
- `/app/backend/sitemap.py` - Sitemap-Generierung, Google Ping, robots.txt
- `/app/backend/trending.py` - Event-Scoring, Trend-Detection
- `/app/backend/data_import.py` - RSS Scraper, LLM Generator, Update-Logik

### Frontend
- `/app/frontend/src/components/TrendingWidget.jsx` - Trending Sidebar + Bar
- `/app/frontend/src/components/RelatedLinks.jsx` - Interne Verlinkung
- `/app/frontend/src/components/SchemaMarkup.jsx` - Schema.org Komponenten

## Google News Checklist
- ✅ Klare Headlines (kein Clickbait)
- ✅ Fakten-Lead im ersten Absatz
- ✅ Autor definiert
- ✅ Veröffentlichungszeit
- ✅ Aktualisierungszeit
- ✅ News Sitemap (48h)
- ✅ Schema.org NewsArticle
- ✅ Update statt Duplikate
- ✅ Interne Verlinkung
- ✅ Große Bilder (min. 1200px)

## Preview URL
https://deploy-transfers.preview.emergentagent.com
