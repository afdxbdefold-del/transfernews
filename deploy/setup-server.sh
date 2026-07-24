#!/bin/bash
# ===========================================
# Hetzner Server Setup Script für TransferNews
# ===========================================

set -e

echo "🚀 TransferNews Server Setup"
echo "============================"

# System updaten
echo "📦 System wird aktualisiert..."
apt update && apt upgrade -y

# Docker installieren
echo "🐳 Docker wird installiert..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# Docker Compose Plugin
echo "🔧 Docker Compose wird installiert..."
apt install -y docker-compose-plugin

# Git installieren
echo "📥 Git wird installiert..."
apt install -y git

# Projektverzeichnis erstellen
echo "📁 Projektverzeichnis wird erstellt..."
mkdir -p /opt/transfernews
cd /opt/transfernews

# Firewall konfigurieren (falls ufw aktiv)
if command -v ufw &> /dev/null; then
    echo "🔒 Firewall wird konfiguriert..."
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
fi

echo ""
echo "✅ Server-Setup abgeschlossen!"
echo ""
echo "Nächste Schritte:"
echo "1. Projekt auf Server kopieren:"
echo "   scp -r /app/* root@DEINE_SERVER_IP:/opt/transfernews/"
echo ""
echo "2. Oder mit Git klonen:"
echo "   cd /opt/transfernews"
echo "   git clone DEIN_REPO_URL ."
echo ""
echo "3. Frontend bauen:"
echo "   cd /opt/transfernews/frontend"
echo "   npm install && npm run build"
echo ""
echo "4. Caddyfile anpassen (Domain eintragen):"
echo "   nano /opt/transfernews/Caddyfile"
echo ""
echo "5. Starten:"
echo "   cd /opt/transfernews"
echo "   docker compose up -d"
echo ""
