#!/bin/bash
set -e

echo "=== Transcriptor v2.1.0 (Docker) ==="

# Cleanup on exit
cleanup() {
    echo "Apagando servicios..."
    kill %1 %2 %3 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

# Display virtual (sin GPU)
Xvfb :99 -screen 0 1280x720x24 +extension RANDR &
sleep 2

# Gestor de ventanas mínimo
fluxbox &
sleep 1

# VNC sobre el display virtual
x11vnc -display :99 -forever -nopw -quiet -listen 0.0.0.0 &
sleep 1

# noVNC: túnel WebSocket para acceder desde navegador
websockify --web /usr/share/novnc 6080 localhost:5900 &
sleep 1

echo ""
echo "  Transcriptor disponible en:"
echo "  → http://localhost:6080  (navegador)"
echo "  → VNC en localhost:5900   (cliente VNC)"
echo ""

# Lanzar la aplicación
cd /app && python app.py
