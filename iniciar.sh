#!/usr/bin/env bash
# Uso: ./iniciar.sh [iniciar|detener|logs]
set -euo pipefail
cd "$(dirname "$0")"
if command -v podman >/dev/null; then C="podman compose"; else C="docker compose"; fi

if [ ! -f .env ]; then
  read -rsp "Contraseña del administrador (10+ caracteres, mayúsculas, minúsculas y números): " pw; echo
  cat > .env <<ENV
SECRET_KEY=$(openssl rand -hex 32)
ADMIN_USER=admin
ADMIN_PASSWORD=$pw
DEMO_DATA=0
RESPALDO_DESTINO=
ENV
  chmod 600 .env
fi

case "${1:-iniciar}" in
  iniciar) $C up -d --build && echo "Listo: http://localhost:8080  (API: /api/docs)" ;;
  detener) $C down ;;
  logs) $C logs -f ;;
  *) echo "Uso: $0 [iniciar|detener|logs]"; exit 1 ;;
esac
