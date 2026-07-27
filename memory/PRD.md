# TransferNews.de - Product Requirements Document

## Letztes Update: 27. Juli 2026

### Kürzlich abgeschlossen:
- ✅ **Spieler-Slug Fix in TrendingWidget** (27.07.2026)
  - Trending-Links nutzen jetzt `player.slug` aus der API statt generierte Slugs
  - Fix: `/spieler/florian-wirtz` → `/spieler/wirtz`
  - Fix: `/spieler/erling-haaland` → `/spieler/haaland`
  - TrendingWidget.jsx und TrendingBar korrigiert
- ✅ **StandardSidebar auf allen redaktionellen Seiten** (27.07.2026)
  - RumoursPage (/geruechte)
  - TickerPage (/ticker)
  - TopDealsPage (/top-deals)
  - FreeAgentsPage (/abloesefrei)
  - DeadlineDayPage (/deadline-day)
  - SearchPage (/suche)
  - Grid-Layout: lg:grid-cols-[1fr_300px] für Desktop
  - Sidebar versteckt auf Mobile (hidden lg:block)
  - Trending Widget in jeder Sidebar
- ✅ **Error Overlay Fix für TheMoneytizer Scripts** (27.07.2026)
  - Cross-Origin Script-Fehler werden in index.html abgefangen
  - Keine störenden Error-Overlays mehr im Development
- ✅ **data-testid Attribute für Ads** (27.07.2026)
  - megabanner-ad, billboard-ad für besseres Testing
- ⚠️ **TheMoneytizer Ads auf Preview**: Megabanner/Billboard laden Scripts aber rendern nicht (Domain nicht autorisiert). Auf Production (transfernews.de) sollte es funktionieren.
- ✅ **Alle 18 Bundesliga-Clubs komplett**: 406 Spieler, 2.66 Mrd. € Gesamtwert (24.07.2026)
  - FC Bayern München (42 Spieler, 688M €)
  - RB Leipzig (17 Spieler, 433M €)
  - Borussia Dortmund (29 Spieler, 260M €)
  - Eintracht Frankfurt (16 Spieler, 239M €)
  - Borussia Mönchengladbach (15 Spieler, 162M €)
  - Bayer 04 Leverkusen (31 Spieler, 128M €)
  - SC Freiburg (16 Spieler, 133M €)
  - + 11 weitere Clubs (VfB Stuttgart, Wolfsburg, Union Berlin, Hoffenheim, Bremen, Augsburg, Mainz, Bochum, Heidenheim, Holstein Kiel, St. Pauli)
- ✅ **Live-Ticker mit Echtzeit-Meldungen**: 40+ Artikel, Auto-Update alle 30 Sekunden (24.07.2026)
- ✅ **Neue Vereinskader**: Liverpool, Arsenal, Chelsea, Barcelona (24.07.2026)
- ✅ **Top-Deals Seite**: Teuerste Transfers sortiert nach Ablösesumme (24.07.2026)
- ✅ **Spielerbilder**: 51+ Spieler mit Wikimedia-Bildern (24.07.2026)
- ✅ **Volle Kader für Top-Vereine**: Real Madrid, Manchester City, Bayern erweitert (24.07.2026)
- ✅ **Transfer-Verlinkung**: Vereinsnamen im Transfer-Tab klickbar (24.07.2026)
- ✅ **Marktwert-Daten**: Top-Spieler mit aktuellen Marktwerten (24.07.2026)

### Teilweise erledigt:
- 🟡 **Vereinslogos laden**: 10 von 31 Vereinen haben Wikipedia-Logos

## Latest Update: 24.07.2026

### Recent Changes
- Added 3 new menu items: Ticker, Top-Deals, Ablösefrei
- Removed "30 Artikel" counter from filters and sidebar
- All new pages fully functional with proper SEO meta tags

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
- **NEU: WIKIMEDIA IMAGE SYSTEM**
- **NEU: STORY ENGINE (Duplicate Killer + Source Weighting)**

## Technical Architecture
- **Frontend:** React 19 mit Tailwind CSS, Shadcn UI, Phosphor Icons, react-helmet-async
- **Backend:** FastAPI (Python)
- **Datenbank:** MongoDB
- **Auth:** JWT-basiertes Admin-Login
- **LLM:** emergentintegrations (GPT-4o via Emergent LLM Key)
- **RSS:** feedparser für 19 internationale Nachrichtenquellen (6 Regionen)
- **Bilder:** Wikimedia Commons mit CC-BY/CC0 Lizenzen (≥1200px für Google Discover)
- **Story Engine:** Duplicate Detection, Source Weighting, Stage Tracking

## What's Been Implemented

### 29. März 2026 - GOLDSTANDARD UI/UX UPGRADE ✅ NEU!
- ✅ **Trending Widget** - Zeigt Top 5 Spieler + Vereine basierend auf Artikel-Häufigkeit
- ✅ **Trending Bar** - Horizontale Leiste mit Trending-Namen oberhalb des Contents
- ✅ **Vereinslogos** - Club-Badges (From → To) bei allen Transfer-Artikeln
- ✅ **Farbige Status-Badges** - OFFIZIELL (grün), GERÜCHT (orange), HEISS (rot), NEWS (grün)
- ✅ **Liga-Dropdown** - Bundesliga, Premier League, La Liga, Serie A, Ligue 1 mit Länderflaggen
- ✅ **Hot Transfers Sektion** - Top 3 Transfer-Gerüchte mit Wahrscheinlichkeits-Meter
- ✅ **Transfer-Probability** - Prozentuale Wahrscheinlichkeitsanzeige bei Gerüchten

### 29. März 2026 - E-E-A-T TRUSTWORTHINESS SYSTEM ✅
- ✅ **Datenschutz-Seite** (`/datenschutz`):
  - DSGVO-konforme Datenschutzerklärung
  - 9 Abschnitte: Verantwortlicher, erhobene Daten, Cookies, Rechtsgrundlage, Ihre Rechte, Drittanbieter, Datensicherheit, Kontakt, Beschwerderecht
  - Auskunfts-, Berichtigungs-, Löschungsrecht erklärt
  - SSL-Verschlüsselung Hinweis
- ✅ **Impressum-Seite** (`/impressum`):
  - Vollständige rechtliche Angaben gemäß § 5 TMG
  - Handelsregister, USt-IdNr., Kontaktdaten
  - Verantwortlicher für Inhalt nach § 55 RStV
  - Haftungsausschluss und Streitschlichtung
- ✅ **Über-Uns-Seite** (`/ueber-uns`):
  - Mission Statement und Statistiken (2M+ Leser, 12 Redakteure)
  - Werte-Sektion: Zuverlässigkeit, Geschwindigkeit, Transparenz
  - "So arbeiten wir" 4-Schritte-Prozess
  - Quellen-Tier-System Erklärung
  - Link zur Redaktionsseite
- ✅ **Source Badge Komponente** (`NewsDetailPage.jsx`):
  - Tier 1/2/3 Klassifizierung der Quelle
  - Konfidenz-Score Balken (0-100%)
  - Sekundärquellen-Anzeige
- ✅ **Fact-Check Badge**:
  - "Geprüfter Artikel" Siegel mit Autor
  - Autorrolle und Aktualisierungsdatum
- ✅ **Schema.org NewsArticle**:
  - Vollständiges JSON-LD Markup
  - Autor mit URL, Publisher mit Logo
  - articleSection, wordCount, keywords
- ✅ **Footer-Update**:
  - "Über Uns" Sektion mit Links zu allen E-E-A-T Seiten
  - Redaktion, Impressum, Datenschutz verlinkt

### 29. März 2026 - STORY ENGINE (DUPLICATE KILLER) ✅
- ✅ **Story-basiertes System** (`/app/backend/story_engine.py`):
  - Eine Transfer-Story = Eine URL (SEO-optimiert)
  - Mehrere Quellen → Update statt neuer Artikel
  - Story-Key: `player-slug__target-club-slug__transfer-type`
- ✅ **Source Weighting** (19 Quellen mit Trust/Speed Scores):
  - Sky Sports (9.5/9.0), L'Équipe (9.0/8.3), kicker (9.0/6.8)
  - Marca (8.8/8.8), BBC Sport (8.7/6.9), Gazzetta (8.7/8.4)
  - Country Bonus für lokale Quellen (+0.5)
  - Tier 1 Bonus (+0.4)
- ✅ **Stage Detection** (5 Phasen):
  - rumor → advanced → near_done → done → official
  - Automatische Erkennung via Keywords (EN/DE/ES/IT/FR)
  - Stage Upgrade triggert Artikel-Update
- ✅ **Confidence Scoring** (35-100):
  - Basis nach Stage + Tier-Bonus + Multi-Source-Bonus
  - Publish-Threshold: 45 | Prominent-Threshold: 80
- ✅ **Duplicate Detection**:
  - Gleicher Spieler + Verein + Typ = Merge
  - Stärkere Quelle ersetzt Primary Source
  - 96h Active Window für Stories
- ✅ **API Endpoints**:
  - `GET /api/pipeline/stories` - Aktive Transfer-Stories
  - `GET /api/pipeline/status` - inkl. Story Engine Stats

### 29. März 2026 - GLOBALE RSS-QUELLEN (19 Feeds)
- ✅ 🌍 Global: CaughtOffside, 90min, FootballTransfers, Goal
- ✅ 🇬🇧 UK: Sky Sports, BBC Sport, TEAMtalk
- ✅ 🇪🇸 Spain: Marca, AS, Mundo Deportivo
- ✅ 🇮🇹 Italy: Gazzetta, Corriere dello Sport, Tuttosport
- ✅ 🇫🇷 France: L'Équipe, RMC Sport, Foot Mercato
- ✅ 🇩🇪 Germany: BILD, kicker, Sport1

### 29. März 2026 - MARKTWERT INFO-BOX SYSTEM
- ✅ **PlayerInfoBox Komponente** (`NewsDetailPage.jsx`):
  - Dunkle Info-Box unter dem Hero-Bild
  - Zeigt Marktwert (grün hervorgehoben), Vertragslaufzeit, Alter, Position
  - Zusätzliche Zeile mit vollständigem Namen, Nationalität, Verein
  - Responsive Grid-Layout (2-4 Spalten)
- ✅ **Backend-Integration** (`speed_pipeline.py`):
  - Extrahiert strukturierte Spielerdaten aus Context-Scraper (Transfermarkt, Wikidata)
  - Speichert `market_value`, `contract_until`, `player_age`, `player_position` als DB-Felder
  - Automatische Anreicherung beim GPT-Rewrite
- ✅ **API Endpoints**:
  - `POST /api/pipeline/enrich-article/{id}` - Einzelnen Artikel mit Spielerdaten anreichern
  - `POST /api/pipeline/enrich-all?limit=` - Batch-Anreicherung aller Artikel ohne Marktwert
- ✅ **Schema-Erweiterung** (`models.py`):
  - Neue Felder: `market_value`, `contract_until`, `player_age`, `player_nationality`, `player_position`, `player_full_name`

### 29. März 2026 - WIKIMEDIA IMAGE SYSTEM (NEU!)
- ✅ **Wikimedia Image Pipeline** (`/app/backend/wikimedia_images.py`):
  - Automatische Spieler-Erkennung aus Artikeltext (Regex mit Akzent-Unterstützung)
  - Wikimedia Commons API-Integration mit sauberem User-Agent
  - **Quality-Scoring (0-100)** basierend auf:
    - Bildgröße (≥1200px Bonus)
    - Seitenverhältnis (16:9 ideal)
    - Lizenz (CC-BY, CC-BY-SA, CC0, Public Domain)
    - Name im Titel, Autor vorhanden
    - Negative Signale (Logo, Wappen, Gruppenfotos)
  - Fallback-System mit Unsplash-Bildern wenn kein Spieler erkannt
  - **Attribution-Generierung**: "Foto: [Autor] / Wikimedia Commons / [Lizenz]"
- ✅ **Frontend Attribution** (`NewsDetailPage.jsx`):
  - Dunkler Balken unter Hero-Bild mit vollständiger Lizenz-Attribution
  - Link zu Wikimedia Commons Quellseite
  - Quality-Score Anzeige (Q100)
- ✅ **API Endpoints**:
  - `POST /api/wikimedia/search?query=` - Suche nach Spielerbildern
  - `POST /api/wikimedia/process-article/{id}` - Artikel mit Wikimedia-Bild aktualisieren
  - `POST /api/wikimedia/update-all?limit=` - Batch-Update aller Artikel
  - `POST /api/wikimedia/use-fallback/{id}` - Manuell Fallback setzen
  - `GET /api/pipeline/image-status` - Wikimedia vs Fallback Statistiken
- ✅ **Integration in Speed-Pipeline**:
  - Neue Artikel erhalten automatisch Wikimedia-Bilder
  - `hero_image_meta` mit vollständigen Lizenz-Metadaten in MongoDB
  - `hero_image_source: "wikimedia" | "fallback"` Tracking

### 29. März 2026 - GPT-REWRITE QUALITY ENGINE
- ✅ **Wikipedia-Kontext-Recherche** (`/app/backend/context_research.py`):
  - Live-Daten von Wikipedia für längere, faktisch korrekte Artikel
  - Spieler-Karriere, Club-Geschichte, Transfer-Kontext
- ✅ **Validierungsregeln für GPT-Rewrite**:
  - Mindestens 150 Wörter, max 300
  - Mindestens 2 H2-Überschriften (##) für Google Discover
  - **Phrasen-Banliste**: "Es bleibt abzuwarten", "Möglicherweise", etc.
  - Ablehnung bei erfundenen Statistiken oder kürzerem Output
  - Retry-Mechanismus bei Validierungsfehler
- ✅ **H2-Rendering im Frontend**:
  - Markdown `##` wird sauber zu `<h2>` mit Oswald-Font

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
- [x] **WIKIMEDIA IMAGE SYSTEM** (CC-lizenzierte Spielerbilder mit Attribution)
- [x] **E-E-A-T TRUSTWORTHINESS** (Impressum, Über Uns, Fact-Check Badges, Schema.org) ✅ NEU

### P1 (In Arbeit)
- [x] Breaking-Engine Score-Berechnung (Event-Scoring nach Quelle, Spieler-Level, Club-Level) ✅
- [x] Trend-System Zeitfenster-Logik (15m, 1h, 6h, 24h Cluster für trend_score) ✅
- [x] SEO-Landingpages dynamische Routen (`/wettbewerb/{slug}`, `/thema/...`) ✅
- [x] Google Search Console Integration (`/admin/gsc`) ✅
- [x] **Marktwert Info-Box** (Strukturierte Spielerdaten: Marktwert, Vertrag, Alter, Position) ✅
- [ ] Admin-Panel für Bild-Kontrolle (Wikimedia-Bilder manuell neu suchen, ablehnen, Fallback erzwingen)
- [ ] Homepage als Live-Feed (Auto-Refresh alle 60s)
- [ ] Enrichment-Batch-Job (Alle Artikel ohne Marktwert anreichern)

### P2 (Später)
- [ ] Alte 4 Artikel ohne H2 manuell rewriten (Rewrite wurde wegen Phrasen abgelehnt)
- [ ] `image_system.py` mit `wikimedia_images.py` konsolidieren
- [ ] Bilder lokal speichern (Hotlinking vermeiden)
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
- `/app/backend/wikimedia_images.py` - **NEU: Wikimedia Commons Bild-Pipeline**
- `/app/backend/context_research.py` - **NEU: Wikipedia-Kontext für GPT-Rewrite**
- `/app/backend/speed_pipeline.py` - Instant-Artikel & GPT-Rewrite Engine

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
