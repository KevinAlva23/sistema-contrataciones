#!/usr/bin/env bash
# Uso: ./respaldo.sh | ./respaldo.sh listar | ./respaldo.sh restaurar ARCHIVO
set -euo pipefail
cd "$(dirname "$0")"
if command -v podman >/dev/null; then RT=podman; else RT=docker; fi
C="$RT compose"
mkdir -p respaldos

case "${1:-crear}" in
  crear)
    A="respaldos/contrataciones-$(date +%Y%m%d-%H%M%S).db"
    $C exec -T backend rm -f /tmp/r.db
    $C exec -T backend python -c "import sqlite3; sqlite3.connect('/data/contrataciones.db').execute(\"VACUUM INTO '/tmp/r.db'\")"
    $C exec -T backend cat /tmp/r.db > "$A"
    $C exec -T backend rm -f /tmp/r.db
    ls -1t respaldos/*.db | tail -n +15 | xargs -r rm --
    echo "Respaldo creado: $A"
    # Copia fuera del equipo si defines RESPALDO_DESTINO en .env
    DEST=$(grep -E '^RESPALDO_DESTINO=' .env 2>/dev/null | cut -d= -f2- || true)
    if [ -n "$DEST" ]; then rsync -a "$A" "$DEST" && echo "Copiado a $DEST"; fi ;;
  listar) ls -lh respaldos ;;
  restaurar)
    F="${2:?Indica el archivo, p. ej. respaldos/contrataciones-2026....db}"
    read -rp "Esto reemplaza la base actual. ¿Continuar? (si/no) " r; [ "$r" = si ] || exit 1
    $C stop backend
    $RT run --rm -v contrataciones_datos:/data -v "$PWD/$F":/r.db:ro python:3.12-slim \
      sh -c "cp /r.db /data/contrataciones.db && chown 10001 /data/contrataciones.db"
    $C start backend && echo "Restaurado." ;;
  *) echo "Uso: $0 [crear|listar|restaurar ARCHIVO]"; exit 1 ;;
esac
