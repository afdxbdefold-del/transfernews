# Nginx Reverse Proxy Setup (ersetzt Coolify-Proxy)

## Voraussetzungen
- Let's Encrypt Zertifikat vorhanden unter `/etc/letsencrypt/live/transfernews.de/`
- Frontend-Container läuft im Netzwerk `t4iysn7locgn8jdax7xb6s9j_app-network`

---

## Schritt 1: Coolify-Proxy stoppen

```bash
docker stop coolify-proxy
docker update --restart=no coolify-proxy
```

Der zweite Befehl verhindert, dass der Container nach Server-Neustart automatisch wieder startet.

---

## Schritt 2: Nginx-Konfiguration erstellen

```bash
mkdir -p /opt/nginx-proxy
cat > /opt/nginx-proxy/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Upstream - verwendet Docker DNS
    upstream frontend {
        server frontend:80;
    }

    # HTTP -> HTTPS Redirect
    server {
        listen 80;
        server_name transfernews.de www.transfernews.de;
        return 301 https://$host$request_uri;
    }

    # HTTPS Server
    server {
        listen 443 ssl http2;
        server_name transfernews.de www.transfernews.de;

        ssl_certificate /etc/letsencrypt/live/transfernews.de/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/transfernews.de/privkey.pem;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

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
EOF
```

**Wichtig:** Der Upstream `frontend` nutzt Docker-DNS. Coolify erstellt Container mit Alias `frontend` im App-Netzwerk, unabhängig vom dynamischen Container-Namen.

---

## Schritt 3: Nginx-Proxy starten

```bash
docker run -d \
  --name nginx-proxy \
  --restart always \
  --network t4iysn7locgn8jdax7xb6s9j_app-network \
  -p 80:80 \
  -p 443:443 \
  -v /opt/nginx-proxy/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v /etc/letsencrypt:/etc/letsencrypt:ro \
  -v /var/log/nginx:/var/log/nginx \
  nginx:alpine
```

---

## Schritt 4: Testen

```bash
# HTTP Redirect prüfen
curl -I http://transfernews.de/

# HTTPS prüfen
curl -I https://transfernews.de/

# API Health prüfen
curl https://transfernews.de/api/health
```

Erwartete Ergebnisse:
- HTTP: `301 Moved Permanently` → HTTPS
- HTTPS: `200 OK` mit HTML
- API Health: `{"status":"healthy",...}`

---

## Fehlerbehebung

### Falls "frontend" nicht auflösbar ist

Prüfen Sie den Network-Alias:
```bash
docker inspect $(docker ps --format "{{.Names}}" | grep frontend | head -1) \
  --format '{{json .NetworkSettings.Networks}}' | jq .
```

Falls kein `frontend` Alias existiert, ermitteln Sie die Container-IP:
```bash
FRONTEND_IP=$(docker inspect $(docker ps --format "{{.Names}}" | grep frontend | head -1) \
  --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
echo "Frontend IP: $FRONTEND_IP"
```

Dann in `/opt/nginx-proxy/nginx.conf` ersetzen:
```
upstream frontend {
    server <FRONTEND_IP>:80;
}
```

Und Nginx neu starten:
```bash
docker restart nginx-proxy
```

### Nach Coolify-Redeploy

Falls Coolify das Frontend neu deployt und die IP sich ändert:
```bash
# Neue IP ermitteln
FRONTEND_IP=$(docker inspect $(docker ps --format "{{.Names}}" | grep frontend | head -1) \
  --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')

# Nginx-Config aktualisieren
sed -i "s/server [0-9.]*:80;/server $FRONTEND_IP:80;/" /opt/nginx-proxy/nginx.conf

# Nginx neu laden
docker exec nginx-proxy nginx -s reload
```

---

## Zertifikat-Erneuerung

Das vorhandene Certbot-Setup erneuert automatisch. Nach Erneuerung:
```bash
docker exec nginx-proxy nginx -s reload
```

Optional als Certbot-Hook in `/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh`:
```bash
#!/bin/bash
docker exec nginx-proxy nginx -s reload
```
Dann: `chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh`
