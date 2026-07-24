# TransferNews - Hetzner Deployment Anleitung

## Voraussetzungen
- Hetzner Cloud Server (CX21 empfohlen)
- Domain mit DNS auf Server-IP zeigend
- SSH Zugang zum Server

---

## Schnellstart (5 Minuten)

### 1. Per SSH auf Server verbinden
```bash
ssh root@DEINE_SERVER_IP
```

### 2. Setup-Script ausführen
```bash
curl -sSL https://raw.githubusercontent.com/DEIN_REPO/main/deploy/setup-server.sh | bash
```

Oder manuell:
```bash
apt update && apt install -y docker.io docker-compose-plugin git
mkdir -p /opt/transfernews
```

### 3. Projekt auf Server kopieren

**Option A: Mit Git (empfohlen)**
```bash
cd /opt/transfernews
git clone https://github.com/DEIN_USERNAME/transfernews.git .
```

**Option B: Mit SCP (von deinem PC)**
```bash
scp -r /app/* root@DEINE_SERVER_IP:/opt/transfernews/
```

### 4. Domain konfigurieren

Caddyfile bearbeiten:
```bash
nano /opt/transfernews/Caddyfile
```

Ersetze `transfernews.de` mit deiner Domain.

### 5. Frontend bauen

```bash
cd /opt/transfernews/frontend
npm install
npm run build
```

### 6. Starten!

```bash
cd /opt/transfernews
docker compose up -d
```

---

## Befehle

| Aktion | Befehl |
|--------|--------|
| Status prüfen | `docker compose ps` |
| Logs ansehen | `docker compose logs -f` |
| Neustart | `docker compose restart` |
| Stoppen | `docker compose down` |
| Update deployen | `./deploy/deploy.sh` |

---

## SSL/HTTPS

Caddy holt automatisch ein Let's Encrypt Zertifikat.
Voraussetzung: DNS muss auf den Server zeigen!

Prüfen:
```bash
dig +short transfernews.de
# Sollte deine Server-IP zeigen
```

---

## Backup

### Datenbank sichern
```bash
docker exec transfernews-db mongodump --out /dump
docker cp transfernews-db:/dump ./backup-$(date +%Y%m%d)
```

### Datenbank wiederherstellen
```bash
docker cp ./backup-DATUM transfernews-db:/dump
docker exec transfernews-db mongorestore /dump
```

---

## Troubleshooting

### Container startet nicht
```bash
docker compose logs backend
docker compose logs mongodb
```

### SSL funktioniert nicht
- DNS prüfen: `dig +short deine-domain.de`
- Ports prüfen: `curl -I http://deine-domain.de`
- Caddy Logs: `docker compose logs caddy`

### MongoDB Verbindungsfehler
```bash
docker compose exec backend ping mongodb
```

---

## Kosten

| Service | Monatlich |
|---------|-----------|
| Hetzner CX21 | ~€4.50 |
| Domain | ~€1.00 |
| SSL | kostenlos |
| **Gesamt** | **~€5.50** |
