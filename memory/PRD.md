# TransferNews.de - Product Requirements Document

## Original Problem Statement
Deutschsprachige Fußball-Transfer-News-Plattform auf der Domain transfernews.de mit:
- Transfer-News, Gerüchte, bestätigte Transfers, offizielle Wechsel
- Spielerseiten, Vereinsseiten, Wettbewerbsseiten
- Automatische News-Generierung aus strukturierten Rohdaten
- LLM-basierte Multi-Source Artikel-Generierung
- Zentrales Dashboard zur Verwaltung der Werbespots
- **Layout: Pixel-perfekte Kopie von sport1.de**
- **Content: Streng limitiert auf Fußball-Transfers**
- **Bilder: Original-Bilder oder Spieler-spezifische Suche**
- **SEO: Google Discover optimiert**
- **NEU: TREND + BREAKING + SEO-LANDINGPAGE-SYSTEM**

## Technical Architecture
- **Frontend:** React 19 mit Tailwind CSS, Shadcn UI, Phosphor Icons, react-helmet-async
- **Backend:** FastAPI (Python)
- **Datenbank:** MongoDB
- **Auth:** JWT-basiertes Admin-Login
- **LLM:** emergentintegrations (GPT-4o via Emergent LLM Key)
- **RSS:** feedparser für 6 deutsche Nachrichtenquellen
- **Bilder:** aiohttp für Downloads, Unsplash/Pexels für Stadionbilder

## User Personas
1. **Fußball-Fan:** Besucht Seite für Transfer-News und Gerüchte
2. **Admin/Redakteur:** Verwaltet Inhalte über Dashboard
3. **Werbepartner:** Platziert Anzeigen über Ad-Slots

## Core Requirements (Implemented)

### TREND + BREAKING + SEO-LANDINGPAGE-SYSTEM (NEU - März 2026)
- [x] **Backend trending.py:** Event-Scoring-System (Spieler-/Club-Popularität, Quellen-Vertrauen, Breaking-Keywords)
- [x] **Backend trending.py:** Trend-Detection (trending_players, trending_clubs nach Zeitfenster)
- [x] **Backend trending.py:** Duplicate-Detection & Auto-Update-Logik für Artikel
- [x] **Backend trending.py:** SEO-Landingpage-Daten (Spieler/Club-Aggregation)
- [x] **Backend server.py:** API-Endpoints für Trending/Breaking/Landing
  - `GET /api/trending/all` - Alle Trending-Daten
  - `GET /api/trending/players` - Trending Spieler
  - `GET /api/trending/clubs` - Trending Vereine
  - `GET /api/breaking` - Breaking News
  - `GET /api/landing/spieler/{slug}` - Spieler-Landingpage
  - `GET /api/landing/verein/{slug}` - Vereins-Landingpage
  - `GET /api/landing/abloesefreie` - Ablösefreie Transfers
  - `GET /api/landing/top-transfers` - Top-Transfers
  - `GET /api/public/news` - Public News mit Filter
  - `GET /api/public/news/{slug}` - News mit Related Links
- [x] **Frontend TrendingWidget.jsx:** Sidebar-Widget mit Spieler- und Club-Rankings
- [x] **Frontend TrendingBar.jsx:** Horizontale Trending-Bar für Mobile
- [x] **Frontend RelatedLinks.jsx:** Auto-generierte interne Verlinkung
- [x] **Frontend SchemaMarkup.jsx:** Schema.org JSON-LD Komponenten
- [x] **SEO Schema.org:** Person, SportsTeam, WebSite JSON-LD Markup

### Content Pipeline
- [x] RSS Scraper für 6 Quellen (Welt, Spiegel, Zeit, FAZ, SZ, T-Online)
- [x] Strenge Transfer-Keywords-Filterung
- [x] Multi-Source LLM Artikel-Generierung (Google Discover optimiert)
- [x] Lokale Bildspeicherung (`/api/static/images/`)
- [x] Stadion-Panoramas mit Vereinswappen-Overlay

### SEO & Google Discover
- [x] react-helmet-async Integration
- [x] Schema.org NewsArticle JSON-LD
- [x] Schema.org Person JSON-LD (PlayerPage)
- [x] Schema.org SportsTeam JSON-LD (ClubPage)
- [x] Schema.org WebSite JSON-LD (HomePage)
- [x] OpenGraph & Twitter Card Meta-Tags
- [x] `robots: max-image-preview:large` für Google Discover

### Public Pages
- [x] Startseite mit sport1.de-Style Layout
- [x] Breaking News Ticker (rot, animiert)
- [x] Hero-Teaser mit Gradient-Overlay
- [x] Newsticker-Sidebar mit Zeit-Badges
- [x] **TrendingWidget in Sidebar** (NEU)
- [x] News-Übersicht mit Newsticker-Style
- [x] News-Detailseite mit Share-Buttons + SEO-Tags + **Related Links** (NEU)
- [x] Spielerseite mit Tabs + **Schema.org SEO** (NEU)
- [x] Vereinsseite mit Tabs + **Schema.org SEO** (NEU)
- [x] Wettbewerbsseite mit Tabs
- [x] Gerüchte-Übersicht
- [x] Bestätigte Transfers-Seite
- [x] Suchfunktion mit Autosuggest

### Admin Dashboard
- [x] Login-System mit JWT
- [x] Dashboard-Übersicht mit Statistiken
- [x] Spielerverwaltung (CRUD)
- [x] Vereinsverwaltung (CRUD)
- [x] Wettbewerbsverwaltung (CRUD)
- [x] Quellenverwaltung (CRUD)
- [x] Event-Verwaltung (Scraper-Pipeline)
- [x] Artikelverwaltung (CRUD)
- [x] Transferverwaltung (CRUD)
- [x] Gerüchteverwaltung (CRUD)
- [x] **Ad-Management-System (34 Slots)**

## What's Been Implemented

### 28. März 2026 - TREND + BREAKING + SEO System
- API-Endpoints für Trending/Breaking/Landing-Pages
- TrendingWidget Komponente für Sidebar
- TrendingBar horizontale Komponente
- RelatedLinks für automatische interne Verlinkung
- Schema.org JSON-LD für Person, SportsTeam, WebSite
- Dynamische SEO-Titel für alle Entity-Seiten

### März 2026 - Content Pipeline & SEO
- RSS Feed Scraper (6 deutsche Quellen)
- Strenge Transfer-Keywords-Filterung
- Multi-Source LLM Artikel-Generierung
- Lokale Bildspeicherung
- react-helmet-async SEO Integration
- Schema.org NewsArticle JSON-LD

### März 2026 - Sport1.de Layout Redesign
- Kompletter Frontend-Umbau im sport1.de-Stil
- Neuer zweistufiger Header
- Newsticker-Komponenten mit Zeit-Badges
- Hero-Teaser mit Gradient-Overlay
- Breaking News Ticker
- Status-Badges (GERÜCHT, OFFIZIELL, BESTÄTIGT)
- Transfer-Wahrscheinlichkeits-Balken

## Prioritized Backlog

### P0 (Completed)
- [x] MVP komplett implementiert
- [x] Sport1.de-Style Layout Redesign
- [x] RSS Scraper & LLM Pipeline
- [x] Google Discover SEO Tags
- [x] **TREND + BREAKING + SEO-LANDINGPAGE-SYSTEM**

### P1 (Nächste Phase)
- [ ] Cronjob für automatisches Scraping (APScheduler)
- [ ] Admin "News aktualisieren" Button
- [ ] XML-Sitemap Generator
- [ ] News-Sitemap für Google News
- [ ] Auto-Update Logik: Status-Änderungen bestehender Artikel statt Duplikate

### P2 (Später)
- [ ] Themenseiten (Deadline Day, Sommertransfers, etc.)
- [ ] Newsletter-Integration
- [ ] Echtzeit-Benachrichtigungen
- [ ] Social Media Sharing optimieren
- [ ] Performance-Optimierung (Caching)

## Admin Credentials
- Email: admin@transfernews.de
- Password: admin123

## Key Files

### Backend
- `/app/backend/server.py` - API Endpoints inkl. Trending/Breaking/Landing
- `/app/backend/trending.py` - Event-Scoring, Trend-Detection, Landing-Daten
- `/app/backend/data_import.py` - RSS Scraper, LLM Generator, Bildsuche
- `/app/backend/models.py` - Datenmodelle

### Frontend
- `/app/frontend/src/App.js` - HelmetProvider Wrapper, Routes
- `/app/frontend/src/api.js` - API-Funktionen inkl. Trending/Breaking/Landing
- `/app/frontend/src/components/TrendingWidget.jsx` - Trending Sidebar + Bar
- `/app/frontend/src/components/RelatedLinks.jsx` - Interne Verlinkung
- `/app/frontend/src/components/SchemaMarkup.jsx` - Schema.org Komponenten
- `/app/frontend/src/pages/public/HomePage.jsx` - Homepage + WebsiteSchema
- `/app/frontend/src/pages/public/PlayerPage.jsx` - Spielerseite + PersonSchema
- `/app/frontend/src/pages/public/ClubPage.jsx` - Vereinsseite + SportsTeamSchema
- `/app/frontend/src/pages/public/NewsDetailPage.jsx` - NewsArticle Schema

## Preview URL
https://deploy-transfers.preview.emergentagent.com
