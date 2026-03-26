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

## Technical Architecture
- **Frontend:** React 19 mit Tailwind CSS, Shadcn UI, Phosphor Icons, react-helmet-async
- **Backend:** FastAPI (Python)
- **Datenbank:** MongoDB
- **Auth:** JWT-basiertes Admin-Login
- **LLM:** emergentintegrations (GPT-4o via Emergent LLM Key)
- **RSS:** feedparser für 6 deutsche Nachrichtenquellen
- **Bilder:** aiohttp für Downloads, Unsplash/Pexels für Spielerbilder

## User Personas
1. **Fußball-Fan:** Besucht Seite für Transfer-News und Gerüchte
2. **Admin/Redakteur:** Verwaltet Inhalte über Dashboard
3. **Werbepartner:** Platziert Anzeigen über Ad-Slots

## Core Requirements (Implemented)

### Content Pipeline (NEU - März 2026)
- [x] RSS Scraper für 6 Quellen (Welt, Spiegel, Zeit, FAZ, SZ, T-Online)
- [x] Strenge Transfer-Keywords-Filterung
- [x] Multi-Source LLM Artikel-Generierung (Google Discover optimiert)
- [x] Lokale Bildspeicherung (`/api/static/images/`)
- [x] Spieler-spezifische Bildsuche (extract player names → Unsplash/Pexels)
- [x] `/api/import/full-pipeline` - Komplett-Import mit einem Klick
- [x] `/api/import/refresh-images` - Bilder für bestehende Artikel aktualisieren

### SEO & Google Discover (NEU - März 2026)
- [x] react-helmet-async Integration
- [x] Schema.org NewsArticle JSON-LD
- [x] OpenGraph Meta-Tags
- [x] Twitter Card Meta-Tags
- [x] `robots: max-image-preview:large` für große Bilder in Discover

### Public Pages
- [x] Startseite mit sport1.de-Style Layout
- [x] Breaking News Ticker (rot, animiert)
- [x] Hero-Teaser mit Gradient-Overlay
- [x] Newsticker-Sidebar mit Zeit-Badges
- [x] News-Übersicht mit Newsticker-Style
- [x] News-Detailseite mit Share-Buttons + SEO-Tags
- [x] Spielerseite mit Tabs (News, Transfers, Gerüchte)
- [x] Vereinsseite mit Tabs (News, Transfers)
- [x] Wettbewerbsseite mit Tabs (News, Vereine)
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

### Sport1.de-Style Layout
- [x] Zweistufiger Header (weiß + schwarze Nav-Bar mit grünen Akzenten)
- [x] Logo: TRANSFERNEWS im sport1.de-Stil
- [x] Sport-Navigation mit Tab-Links
- [x] Hero-Teaser-Section mit großem Bild
- [x] Newsticker-Sidebar mit grünen Zeit-Badges
- [x] Breaking News Ticker (rot, animiert)
- [x] Action-Buttons (Transfers, Gerüchte)
- [x] Mobile Hamburger-Menü
- [x] Responsive Design (Desktop + Mobile)
- [x] Markenfarbe #79B92A beibehalten

### Ad-Slots System
- 34 vorkonfigurierte Werbeplätze
- Gruppiert nach Seitentyp (Homepage, News, Player, Club, etc.)
- Steuerbar nach: Name, Slot-Key, Position, Gerätetyp, HTML/JS/Embed Code
- Aktivierung/Deaktivierung ohne Code-Änderung
- Priorität und Feed-Intervall konfigurierbar

### Data Model
- Players, Clubs, Competitions, Sources
- Events (Scraper-Input mit image_url), Transfers, Rumours
- Articles mit verknüpften Entities und feature_image
- Aliases für Entity-Erkennung
- Ad-Slots, Users, Settings

## What's Been Implemented

### März 2026 - Initial Build
- Vollständiges Backend mit 70+ API-Endpoints
- Vollständiges Frontend mit 10 Public Pages + 11 Admin Pages
- JWT-Authentifizierung
- MongoDB Datenmodell
- 34 Ad-Slots initialisiert
- SEO-freundliche URLs
- Responsive Design (Mobile/Desktop)
- Custom SVG Logo
- Markenfarbe #79B92A

### März 2026 - Sport1.de Layout Redesign
- Kompletter Frontend-Umbau im sport1.de-Stil
- Neuer zweistufiger Header
- Newsticker-Komponenten mit Zeit-Badges
- Hero-Teaser mit Gradient-Overlay
- Breaking News Ticker (rot)
- Mobile Hamburger-Menü
- Share-Buttons auf News-Detailseite
- Responsive Layout für Desktop und Mobile

### März 2026 - Content Pipeline & SEO
- RSS Feed Scraper (6 deutsche Quellen)
- Strenge Transfer-Keywords-Filterung
- Multi-Source LLM Artikel-Generierung
- Lokale Bildspeicherung
- Spieler-spezifische Bildsuche (Unsplash/Pexels)
- react-helmet-async SEO Integration
- Schema.org NewsArticle JSON-LD
- OpenGraph & Twitter Card Meta-Tags

## Prioritized Backlog

### P0 (Completed)
- [x] MVP komplett implementiert
- [x] Sport1.de-Style Layout Redesign
- [x] RSS Scraper & LLM Pipeline
- [x] Lokale Bildspeicherung
- [x] Google Discover SEO Tags

### P1 (Nächste Phase)
- [ ] Cronjob für automatisches Scraping (APScheduler)
- [ ] Admin "News aktualisieren" Button
- [ ] XML-Sitemap Generator
- [ ] News-Sitemap für Google News

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
- `/app/frontend/src/App.js` - HelmetProvider Wrapper
- `/app/frontend/src/pages/public/NewsDetailPage.jsx` - SEO-Tags & Schema.org
- `/app/frontend/src/components/Header.jsx` - Zweistufiger Header
- `/app/frontend/src/components/NewsCard.jsx` - Teaser-Komponenten
- `/app/frontend/src/pages/public/HomePage.jsx` - Homepage mit sport1.de-Layout
- `/app/backend/data_import.py` - RSS Scraper, LLM Generator, Bildsuche
- `/app/backend/server.py` - API Endpoints inkl. /import/*

## Preview URL
https://deploy-transfers.preview.emergentagent.com
