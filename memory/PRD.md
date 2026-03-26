# TransferNews.de - Product Requirements Document

## Original Problem Statement
Deutschsprachige Fußball-Transfer-News-Plattform auf der Domain transfernews.de mit:
- Transfer-News, Gerüchte, bestätigte Transfers, offizielle Wechsel
- Spielerseiten, Vereinsseiten, Wettbewerbsseiten
- Automatische News-Generierung aus strukturierten Rohdaten (vorbereitet)
- Aggressive Werbe-Monetarisierung
- Zentrales Dashboard zur Verwaltung der Werbespots
- **Layout: Pixel-perfekte Kopie von sport1.de** (User Requirement, März 2026)

## Technical Architecture
- **Frontend:** React 19 mit Tailwind CSS, Shadcn UI, Phosphor Icons
- **Backend:** FastAPI (Python)
- **Datenbank:** MongoDB
- **Auth:** JWT-basiertes Admin-Login
- **LLM:** OpenAI GPT-5.2 via Emergent LLM Key (vorbereitet)

## User Personas
1. **Fußball-Fan:** Besucht Seite für Transfer-News und Gerüchte
2. **Admin/Redakteur:** Verwaltet Inhalte über Dashboard
3. **Werbepartner:** Platziert Anzeigen über Ad-Slots

## Core Requirements (Implemented)

### Public Pages
- [x] Startseite mit sport1.de-Style Layout
- [x] Breaking News Ticker (rot, animiert)
- [x] Hero-Teaser mit Gradient-Overlay
- [x] Newsticker-Sidebar mit Zeit-Badges
- [x] News-Übersicht mit Newsticker-Style
- [x] News-Detailseite mit Share-Buttons
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
- [x] Event-Verwaltung (Scraper-Pipeline vorbereitet)
- [x] Artikelverwaltung (CRUD)
- [x] Transferverwaltung (CRUD)
- [x] Gerüchteverwaltung (CRUD)
- [x] **Ad-Management-System (34 Slots)**

### Sport1.de-Style Layout (NEW - März 2026)
- [x] Zweistufiger Header (weiß + grüne Nav-Bar)
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
- Events (Scraper-Input), Transfers, Rumours
- Articles mit verknüpften Entities
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

## Prioritized Backlog

### P0 (Completed)
- [x] MVP komplett implementiert
- [x] Sport1.de-Style Layout Redesign

### P1 (Nächste Phase)
- [ ] XML-Sitemap Generator
- [ ] News-Sitemap für Google News
- [ ] Strukturierte Daten (Schema.org)
- [ ] Automatisierter Scraper-Cronjob
- [ ] LLM-basierte Artikel-Generierung aktivieren

### P2 (Später)
- [ ] Themenseiten (Deadline Day, Sommertransfers, etc.)
- [ ] Echtzeit-Benachrichtigungen
- [ ] Newsletter-Integration
- [ ] Social Media Sharing optimieren
- [ ] Performance-Optimierung (Caching)

## Admin Credentials
- Email: admin@transfernews.de
- Password: admin123

## Key Files
- `/app/frontend/src/components/Header.jsx` - Zweistufiger Header
- `/app/frontend/src/components/NewsCard.jsx` - Teaser-Komponenten
- `/app/frontend/src/pages/public/HomePage.jsx` - Homepage mit sport1.de-Layout
- `/app/frontend/src/pages/public/NewsListPage.jsx` - Newsticker-Seite
- `/app/frontend/src/index.css` - Globale Styles

## Preview URL
https://deploy-transfers.preview.emergentagent.com
