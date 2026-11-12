#!/bin/bash
# Uso: ./respaldo.sh | ./respaldo.sh listar | ./respaldo.sh restaurar ARCHIVO.sql
DIR="$(cd "$(dirname "$0")" && pwd)/respaldos"
MANTENER=14
mkdir -p "$DIR"
case "$1" in
  listar) ls -lh "$DIR" ;;
  restaurar)
    [ -f "$2" ] || { echo "Indica un archivo .sql válido (./respaldo.sh listar)"; exit 1; }
    read -p "Esto reemplaza TODOS los datos actuales. ¿Continuar? (si/no) " R
    [ "$R" = "si" ] || { echo "Cancelado."; exit 0; }
    "$0"
    podman exec db psql -U contrataciones -d contrataciones -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    podman exec -i db psql -U contrataciones -d contrataciones < "$2"
    podman restart backend
    echo "Restaurado desde $2" ;;
  *)
    set -e
    DESTINO="$DIR/pg-$(date +%Y-%m-%d_%H-%M).sql"
    podman exec db pg_dump -U contrataciones contrataciones > "$DESTINO"
    chmod 600 "$DESTINO"
    echo "Respaldo creado: $DESTINO"
    ls -1t "$DIR"/pg-*.sql | tail -n +$((MANTENER + 1)) | xargs -r rm -f ;;
esac
