#!/bin/bash
# Uso: ./iniciar.sh   (reconstruye y levanta db + backend + frontend)
#      ./iniciar.sh detener
RED=red-contrataciones
set -a; [ -f .env ] && . ./.env; set +a

if [ "$1" = "detener" ]; then
  podman rm -f frontend backend db
  echo "Detenidos. Los datos se conservan en los volúmenes."
  exit 0
fi
set -e

echo "1/6 Construyendo imágenes..."
podman build -q -t contrataciones_backend ./backend
podman build -q -t contrataciones_frontend ./frontend

echo "2/6 Preparando red y volúmenes..."
podman network exists $RED || podman network create $RED
podman volume exists datos-pg || podman volume create datos-pg

echo "3/6 Limpiando contenedores anteriores..."
podman rm -f frontend backend db 2>/dev/null || true

echo "4/6 Levantando PostgreSQL..."
podman run -d --name db --network $RED -v datos-pg:/var/lib/postgresql/data \
  -e POSTGRES_USER=contrataciones -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  -e POSTGRES_DB=contrataciones --security-opt no-new-privileges \
  --memory 512m --restart unless-stopped docker.io/library/postgres:16-alpine
for i in $(seq 1 40); do
  podman exec db pg_isready -U contrataciones >/dev/null 2>&1 && break
  sleep 1
done

echo "5/6 Levantando backend..."
podman run -d --name backend --env-file .env --network $RED \
  -e DATABASE_URL="postgresql+psycopg2://contrataciones:${POSTGRES_PASSWORD}@db:5432/contrataciones" \
  --read-only --tmpfs /tmp --cap-drop=ALL --security-opt no-new-privileges \
  --memory 512m --pids-limit 200 --restart unless-stopped localhost/contrataciones_backend
for i in $(seq 1 30); do
  podman logs backend 2>&1 | grep -q "Application startup complete" && break
  [ "$(podman inspect -f '{{.State.Running}}' backend)" = "true" ] || { echo "ERROR: backend caído. Ver: podman logs backend"; exit 1; }
  sleep 1
done

echo "6/6 Levantando frontend..."
podman run -d --name frontend --network $RED -p 127.0.0.1:8080:80 \
  --read-only --tmpfs /tmp --tmpfs /var/cache/nginx --tmpfs /var/run \
  --cap-drop=ALL --cap-add=CHOWN --cap-add=SETUID --cap-add=SETGID --cap-add=NET_BIND_SERVICE \
  --security-opt no-new-privileges --memory 256m --pids-limit 200 \
  --restart unless-stopped localhost/contrataciones_frontend
echo "Listo. Abre http://localhost:8080"
