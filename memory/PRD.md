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
- **RSS:** feedparser für 15 internationale Nachrichtenquellen (DE/EN/ES)
- **Bilder:** Unsplash für Google Discover-optimierte Hero-Images (≥1200px)

## What's Been Implemented

### 29. März 2026 - ENTITY & IMAGE SYSTEM für Google Discover
- ✅ **Entity Recognition System** (`/app/backend/entity_recognition.py`):
  - **392 Spieler** mit Metadaten (Position, Nationalität, Popularität, Club)
  - **238 Clubs** mit Liga-Zuordnung und Aliassen
  - Transfer-Typ-Erkennung (Leihe, Permanent, Ablösefrei, Swap, etc.)
  - Confidence-Score für bessere Deduplizierung
  - Spieler aus: Bundesliga, Premier League, La Liga, Serie A, Ligue 1
  - Trainer-Erkennung (Guardiola, Ancelotti, Klopp, Nagelsmann, etc.)
- ✅ **Image System** (`/app/backend/image_system.py`):
  - Automatische Zuweisung von ≥1200px Bildern für Google Discover
  - Club- und Liga-spezifische Bilder
  - `og:image` Tags mit korrekten Dimensionen
  - `twitter:card` Summary Large Image
- ✅ **GPT-Rewrite Fix**:
  - `EMERGENT_LLM_KEY` korrekt in `speed_pipeline.py` integriert
  - Async Rewrite funktioniert jetzt zuverlässig
- ✅ **API Endpoints**:
  - `POST /api/pipeline/update-images` - Bilder für alte Artikel nachträglich zuweisen
  - `GET /api/pipeline/image-status` - Image-Coverage-Status

### 28. März 2026 - SPEED-PIPELINE OPTIMIZATION
- ✅ **Instant-Artikel System** (`/app/backend/speed_pipeline.py`):
  - Artikel in < 100ms erstellen (ohne GPT!)
  - Template-basierte Titel und Bodies
  - Sofort veröffentlicht
- ✅ **Async GPT-Rewrite**:
  - Verbessert Instant-Artikel im Hintergrund
  - Blockiert nicht die Veröffentlichung
- ✅ **Dedupe-System**:
  - Key: Player + Club + Transfer-Type
  - Status-Upgrade statt Duplikate (GERÜCHT → OFFIZIELL)
- ✅ **Schnellere Cronjobs** (`/app/backend/scheduler.py`):
  - RSS: alle 2 Minuten (vorher: 30 Min)
  - Pipeline: alle 1 Minute
  - Sitemap: alle 2 Minuten
  - GPT-Rewrite: alle 5 Minuten
- ✅ **Internal Links System**:
  - Automatische Verlinkung nach Artikel-Erstellung
  - Spieler- und Club-Seiten aktualisiert
- ✅ **API Endpoints**:
  - `POST /api/pipeline/full` - Komplette Pipeline
  - `POST /api/pipeline/rss` - Nur RSS
  - `POST /api/pipeline/process` - Nur Processing
  - `GET /api/pipeline/status` - Pipeline Status

### 28. März 2026 - INTERNATIONALE RSS-QUELLEN
- ✅ **15 RSS-Quellen** konfiguriert (vorher: 6)
- ✅ **Tier-1 International:** Sky Sports UK, ESPN FC, BBC Football
- ✅ **Tier-1 Deutsch:** Transfermarkt, Kicker, Sport1
- ✅ **Tier-2:** Goal.com, Football Italia, Marca, The Guardian
- ✅ **Tier-3:** Sportbuzzer, SPOX, T-Online, Welt, Spiegel
- ✅ **Mehrsprachige Keywords:** DE, EN, ES Transfer-Begriffe
- ✅ **Automatische Übersetzung:** Englische Artikel → Deutsch via LLM
- ✅ **Trust-Score System:** Quellen-Vertrauen beeinflusst Confidence
- ✅ **Filter verbessert:** Rugby, Cricket, Tennis etc. ausgeschlossen

### 28. März 2026 - BREAKING & TREND ENGINE + SEO LANDING PAGES
- ✅ **Erweitertes Event-Scoring** (`/app/backend/trending.py`):
  - Spieler-Popularität (100 Punkte für Mbappé, Haaland etc.)
  - Club-Popularität (100 Punkte für Real Madrid, Bayern etc.)
  - Quellen-Vertrauen (Fabrizio Romano > Sky > Bild)
  - Breaking Keywords (Offiziell, Here We Go, etc.)
  - Zeit-Frische-Bonus (15min = +15, 1h = +12, etc.)
- ✅ **Priority-Zuweisung** (HIGH, MEDIUM, LOW) basierend auf Score
- ✅ **Trend-Zeitfenster** (`/api/trending/windows`):
  - 15 Minuten, 1 Stunde, 6 Stunden, 24 Stunden Cluster
  - `trend_score` Berechnung pro Entity
- ✅ **Wettbewerb-Landingpages** (`/wettbewerb/{slug}`):
  - Bundesliga, Premier League, La Liga, Serie A, Ligue 1, Champions League
  - Breaking News, Gerüchte, Bestätigte Transfers pro Liga
- ✅ **Themen-Landingpages** (`/thema/{slug}`):
  - Ablösefreie Transfers, Deadline Day, Sommertransfers, Wintertransfers
  - Rekordtransfers, Leihen, Junge Talente
- ✅ **API Endpoints**:
  - `GET /api/wettbewerbe` - Liste aller Wettbewerbe
  - `GET /api/wettbewerb/{slug}` - Wettbewerb-Daten
  - `GET /api/themen` - Liste aller Themen
  - `GET /api/thema/{slug}` - Themen-Daten
  - `GET /api/trending/windows` - Zeitfenster-Trends
  - `GET /api/events/score` - Event-Scoring

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
- [x] Breaking-Engine Score-Berechnung (Event-Scoring nach Quelle, Spieler-Level, Club-Level) ✅
- [x] Trend-System Zeitfenster-Logik (15m, 1h, 6h, 24h Cluster für trend_score) ✅
- [x] SEO-Landingpages dynamische Routen (`/wettbewerb/{slug}`, `/thema/...`) ✅
- [x] Google Search Console Integration (`/admin/gsc`) ✅
- [ ] Homepage als Live-Feed (Auto-Refresh alle 60s)

### P2 (Später)
- [ ] Newsletter-Integration
- [ ] Performance-Optimierung (Redis Caching)
- [ ] Push-Benachrichtigungen für Breaking News

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
