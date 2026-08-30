# TransferNews.de - Technische Dokumentation

## Übersicht

TransferNews.de ist eine deutschsprachige Fußball-Transfer-News-Plattform.

- **Frontend:** React (Port 80 intern)
- **Backend:** FastAPI/Python (Port 8001 intern)
- **Datenbank:** MongoDB
- **Hosting:** Hetzner Server mit Coolify
- **Reverse Proxy:** Eigener Nginx (ersetzt Coolify/Traefik)

---

## Server-Architektur

### Container-Struktur (Coolify)

```
nginx-proxy                    → Reverse Proxy (Port 80/443)
frontend-t4iysn7...-*          → React Frontend
backend-t4iysn7...-*           → FastAPI Backend
mongodb-t4iysn7...-*           → MongoDB Datenbank
coolify-redis                  → Redis (Coolify intern, nicht für App)
```

**WICHTIG:** Container-Namen ändern sich bei jedem Coolify-Redeploy!

### Netzwerk

- Coolify Netzwerk: `t4iysn7locgn8jdax7xb6s9j_app-network`
- DNS-Aliase im Netzwerk: `frontend`, `backend`, `mongodb`

---

## Nginx Reverse Proxy

Coolify's Traefik wurde durch eigenen Nginx ersetzt wegen fehlerhafter Routing-Konfiguration.

### Konfiguration: `/opt/nginx-proxy/nginx.conf`

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

### Befehle

```bash
# Nginx neustarten
docker restart nginx-proxy

# Konfiguration neu laden
docker exec nginx-proxy nginx -s reload

# Logs prüfen
docker logs nginx-proxy --tail 50
```

---

## Lokales Repository

**Pfad:** `/opt/transfernews`

**ACHTUNG:** `docker-compose.yml` in diesem Verzeichnis erstellt EIGENE Container mit EIGENER MongoDB!
Diese dürfen NICHT parallel zu Coolify laufen!

```bash
# NIEMALS parallel zu Coolify:
cd /opt/transfernews
docker compose up -d  # ERSTELLT DUPLIKATE!

# Wenn versehentlich gestartet:
docker compose down
```

---

## News-Pipeline

### Ablauf

1. **RSS Scraping** (alle 2 Min) → Events Collection
2. **Speed Pipeline** (alle 1 Min) → Verarbeitet Events → Artikel
3. **GPT Rewrite** (alle 5 Min) → Verbessert Artikel mit OpenAI
4. **Sitemap Update** (alle 2 Min) → Aktualisiert Sitemaps

### Scheduler aktivieren/deaktivieren

```bash
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)

# Status prüfen
docker logs --tail 30 $BACKEND | grep -E "(CRON|scheduler)"

# Scheduler ist in server.py:
# - Aktiviert: start_scheduler() wird aufgerufen
# - Deaktiviert: start_scheduler() auskommentiert
```

### "Unbekannt" Filter

Artikel mit "Unbekannter Spieler" oder "Unbekannter Verein" im Titel werden gefiltert.

Filter in `speed_pipeline.py` Funktion `_create_article_from_story`:

```python
headline = story_result.get("headline", "")
if "nbekannt" in headline.lower():
    return None
```

**Nach Coolify-Redeploy geht dieser Filter verloren!**

### Filter nach Redeploy wiederherstellen

```bash
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)

docker exec $BACKEND sed -i '/async def _create_article_from_story/,/story = story_result.get("story", {})/{s/story = story_result.get("story", {})/story = story_result.get("story", {})\n        headline = story_result.get("headline", "")\n        if "nbekannt" in headline.lower():\n            return None/}' /app/speed_pipeline.py

docker restart $BACKEND
```

---

## OpenAI Integration

### Konfiguration

```bash
# API Key in Backend .env
echo "OPENAI_API_KEY=sk-..." >> /opt/transfernews/backend/.env
```

### Modell

- Aktuell: `gpt-4o-mini`
- Konfiguration in: `speed_pipeline.py` Funktion `_gpt_rewrite_article`

---

## Datenbank-Operationen

### Verbindung

```bash
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)
docker exec $BACKEND python3 -c '
from pymongo import MongoClient
import os
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
# ... Operationen
'
```

### Häufige Operationen

```bash
# Artikel zählen
docker exec $BACKEND python3 -c '
from pymongo import MongoClient
import os
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
print("Published:", db.articles.count_documents({"status": "published"}))
print("Draft:", db.articles.count_documents({"status": "draft"}))
'

# "Unbekannt" Artikel löschen
docker exec $BACKEND python3 -c '
from pymongo import MongoClient
import os
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
r = db.articles.delete_many({"title": {"$regex": "nbekannt", "$options": "i"}})
print("Gelöscht:", r.deleted_count)
'

# Duplikate löschen
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

# Events leeren (für frische RSS-Daten)
docker exec $BACKEND python3 -c '
from pymongo import MongoClient
import os
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
r = db.events.delete_many({})
print("Events gelöscht:", r.deleted_count)
'

# Neueste Artikel anzeigen
docker exec $BACKEND python3 -c '
from pymongo import MongoClient
import os
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
for a in db.articles.find({"status": "published"}).sort("published_at", -1).limit(10):
    print(a.get("title", "")[:60])
'
```

---

## Troubleshooting

### 502 Bad Gateway

1. **Container prüfen:**
```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "backend|frontend|nginx|mongo"
```

2. **Docker-compose Konflikte beseitigen:**
```bash
cd /opt/transfernews
docker compose down
```

3. **Nginx neustarten:**
```bash
docker restart nginx-proxy
```

4. **Backend Logs prüfen:**
```bash
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)
docker logs --tail 50 $BACKEND
```

### Keine neuen News

1. **Scheduler läuft?**
```bash
docker logs --tail 30 $BACKEND | grep -E "(CRON|RSS|SPEED)"
```

2. **Alle Events sind Duplikate?**
```bash
# Events leeren
docker exec $BACKEND python3 -c '
from pymongo import MongoClient
import os
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]
db.events.delete_many({})
print("Events geleert")
'
```

3. **OPENAI_API_KEY fehlt?**
```bash
docker exec $BACKEND printenv | grep OPENAI
```

### API zeigt alte Daten

1. **Richtige MongoDB?** (Docker-compose vs Coolify)
```bash
# Wenn transfernews-mongodb-1 läuft → docker compose down!
docker ps | grep mongo
```

2. **nginx-proxy DNS aktualisieren:**
```bash
docker restart nginx-proxy
```

### Nach Coolify Redeploy

Container-Namen ändern sich! Folgende Schritte:

1. **Docker-compose stoppen (falls läuft):**
```bash
cd /opt/transfernews && docker compose down
```

2. **Nginx neustarten:**
```bash
docker restart nginx-proxy
```

3. **"Unbekannt" Filter wiederherstellen:**
```bash
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)
# Siehe Filter-Befehl oben
```

4. **OPENAI_API_KEY prüfen:**
```bash
docker exec $BACKEND printenv | grep OPENAI
# Falls fehlt: Coolify Environment Variables prüfen
```

---

## Ads Management

### ads.txt

Datei wird von nginx-proxy serviert: `/usr/share/nginx/html/ads.txt`

Enthält Einträge für:
- Primis
- TheMonetizer

### Admin Ad-Slots

- URL: `/admin/ad-slots`
- Ad-Codes können im Admin geändert werden
- Slots werden aus Datenbank geladen

---

## Wichtige Dateien

### Backend
- `/app/server.py` - FastAPI Server + API Endpoints
- `/app/speed_pipeline.py` - News-Pipeline
- `/app/scheduler.py` - Cron Jobs
- `/app/story_engine.py` - Story/Artikel Logik
- `/app/data_import.py` - RSS Import

### Frontend
- `/app/src/App.js` - React Router
- `/app/src/api.js` - API Client
- `/app/src/components/DynamicAds.jsx` - Ad-Komponenten

### Server
- `/opt/transfernews/` - Git Repository
- `/opt/nginx-proxy/nginx.conf` - Nginx Konfiguration
- `/etc/letsencrypt/live/transfernews.de/` - SSL Zertifikate

---

## Bekannte Probleme

1. **Coolify Traefik generiert falsche Labels** → Eigener Nginx-Proxy als Lösung

2. **Container-Namen ändern sich bei Redeploy** → Immer dynamisch ermitteln mit:
   ```bash
   BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)
   ```

3. **Docker-compose und Coolify Konflikt** → NIEMALS beide gleichzeitig!

4. **"Unbekannt" Filter geht bei Redeploy verloren** → Manuell wiederherstellen

5. **RSS Events werden zu Duplikaten** → Events Collection leeren

---

## Deployment Workflow

### Code ändern (ohne Coolify Dashboard)

1. **Änderungen in Emergent machen**
2. **"Save to GitHub" klicken**
3. **Auf Server:**
```bash
cd /opt/transfernews
git pull
# NICHT docker compose verwenden!
```
4. **Coolify deployt automatisch oder manuell triggern**
5. **Nach Redeploy: Nginx neustarten + Filter wiederherstellen**

### Schnelle Änderungen direkt im Container

```bash
BACKEND=$(docker ps --format "{{.Names}}" | grep "backend-t4" | head -1)

# Datei bearbeiten
docker exec -it $BACKEND nano /app/datei.py

# Oder mit sed
docker exec $BACKEND sed -i 's/alt/neu/' /app/datei.py

# Container neustarten
docker restart $BACKEND
```

**ACHTUNG:** Änderungen im Container gehen bei Redeploy verloren!

---

## Kontakt / Support

Bei Problemen:
1. Diese Dokumentation lesen
2. Logs prüfen
3. Container-Status prüfen
4. Bekannte Probleme durchgehen
