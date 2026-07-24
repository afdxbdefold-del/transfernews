#!/bin/bash
# ===========================================
# Deployment Script für TransferNews
# ===========================================

set -e

cd /opt/transfernews

echo "🚀 TransferNews Deployment"
echo "=========================="

# Git Pull (falls Git verwendet wird)
if [ -d ".git" ]; then
    echo "📥 Code wird aktualisiert..."
    git pull origin main
fi

# Frontend bauen
echo "🔨 Frontend wird gebaut..."
cd frontend
npm install --production=false
npm run build
cd ..

# Docker Container neu bauen und starten
echo "🐳 Container werden gestartet..."
docker compose down
docker compose up -d --build

# Aufräumen
echo "🧹 Alte Images werden entfernt..."
docker image prune -f

echo ""
echo "✅ Deployment abgeschlossen!"
echo ""
echo "Status prüfen: docker compose ps"
echo "Logs ansehen:  docker compose logs -f"
