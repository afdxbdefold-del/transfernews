# TransferNews.de - Product Requirements Document

## Original Problem Statement
Deutschsprachige Fußball-Transfer-News-Plattform auf der Domain transfernews.de mit:
- Transfer-News, Gerüchte, bestätigte Transfers, offizielle Wechsel
- Spielerseiten, Vereinsseiten, Wettbewerbsseiten
- Automatische News-Generierung aus strukturierten Rohdaten (vorbereitet)
- Aggressive Werbe-Monetarisierung
- Zentrales Dashboard zur Verwaltung der Werbespots
- Design wie Transfermarkt.de aber in Grün

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
- [x] Startseite mit Breaking News Ticker, News Feed, Sidebar
- [x] News-Übersicht mit Pagination
- [x] News-Detailseite mit SEO-Struktur
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

## What's Been Implemented (2026-03-26)
- Vollständiges Backend mit 70+ API-Endpoints
- Vollständiges Frontend mit 10 Public Pages + 11 Admin Pages
- JWT-Authentifizierung
- MongoDB Datenmodell
- 34 Ad-Slots initialisiert
- SEO-freundliche URLs
- Responsive Design (Mobile/Desktop)
- Transfermarkt-ähnliches Design in Grün

## Prioritized Backlog

### P0 (Ready)
- MVP komplett implementiert

### P1 (Nächste Phase)
- [ ] XML-Sitemap Generator
- [ ] News-Sitemap für Google News
- [ ] Strukturierte Daten (Schema.org)
- [ ] LLM-basierte Artikel-Generierung aktivieren
- [ ] Scraper-Integration für Live-Daten

### P2 (Später)
- [ ] Themenseiten (Deadline Day, Sommertransfers, etc.)
- [ ] Echtzeit-Benachrichtigungen
- [ ] Newsletter-Integration
- [ ] Social Media Sharing optimieren
- [ ] Performance-Optimierung (Caching)

## Admin Credentials
- Email: admin@transfernews.de
- Password: admin123

## Next Tasks
1. Echte Inhalte über Admin-Dashboard erstellen
2. Ad-Codes in Ad-Slots eintragen
3. Sitemap-Generierung implementieren
4. LLM-Integration für News-Generierung aktivieren
