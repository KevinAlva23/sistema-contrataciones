#!/bin/bash
# Construye y levanta el sistema con contenedores separados.
# Uso: ./iniciar.sh          (reconstruye todo)
#      ./iniciar.sh detener  (apaga los contenedores)

RED=red-contrataciones
VOLUMEN=datos

if [ "$1" = "detener" ]; then
  podman rm -f frontend backend
  echo "Contenedores detenidos. Los datos se conservan en el volumen."
  exit 0
fi

# Si algo falla, el script se detiene
set -e

echo "1/5 Construyendo imágenes..."
podman build -q -t contrataciones_backend ./backend
podman build -q -t contrataciones_frontend ./frontend

echo "2/5 Preparando red y volumen..."
podman network exists $RED || podman network create $RED
podman volume exists $VOLUMEN || podman volume create $VOLUMEN

echo "3/5 Limpiando contenedores anteriores..."
podman rm -f frontend backend 2>/dev/null || true

echo "4/5 Levantando backend..."
podman run -d --name backend --env-file .env --network $RED -v $VOLUMEN:/data localhost/contrataciones_backend

# Espera hasta 15 segundos a que el backend arranque
for i in $(seq 1 15); do
  if podman logs backend 2>&1 | grep -q "Application startup complete"; then
    break
  fi
  if [ "$(podman inspect -f '{{.State.Running}}' backend)" != "true" ]; then
    echo "ERROR: el backend se cayó. Revisa: podman logs backend"
    exit 1
  fi
  sleep 1
done

echo "5/5 Levantando frontend..."
podman run -d --name frontend --network $RED -p 8080:80 localhost/contrataciones_frontend

echo "Listo. Abre http://localhost:8080"
