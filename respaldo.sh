#!/bin/bash
# Respaldo y restauración de la base de datos.
# Uso: ./respaldo.sh                 crea un respaldo con fecha
#      ./respaldo.sh listar          muestra los respaldos
#      ./respaldo.sh restaurar ARCHIVO   restaura uno (ej. respaldos/contrataciones-2026-10-29_15-00.db)

DIR="$(cd "$(dirname "$0")" && pwd)/respaldos"
MANTENER=14   # cantidad de respaldos que se conservan
mkdir -p "$DIR"

case "$1" in
  listar)
    ls -lh "$DIR"
    ;;

  restaurar)
    ARCHIVO="$2"
    if [ ! -f "$ARCHIVO" ]; then
      echo "Indica un archivo válido. Usa ./respaldo.sh listar"
      exit 1
    fi
    read -p "Esto reemplaza TODOS los datos actuales. ¿Continuar? (si/no) " R
    [ "$R" = "si" ] || { echo "Cancelado."; exit 0; }
    # Respaldo de seguridad antes de restaurar
    "$0"
    podman stop backend
    podman cp "$ARCHIVO" backend:/data/contrataciones.db
    podman start backend
    echo "Restaurado desde $ARCHIVO"
    ;;

  *)
    set -e
    FECHA=$(date +%Y-%m-%d_%H-%M)
    DESTINO="$DIR/contrataciones-$FECHA.db"
    # .backup es el método seguro de SQLite (no corrompe aunque haya escrituras)
    podman exec backend python3 -c "
import sqlite3
o = sqlite3.connect('/data/contrataciones.db')
d = sqlite3.connect('/data/respaldo_tmp.db')
o.backup(d); d.close(); o.close()
"
    podman cp backend:/data/respaldo_tmp.db "$DESTINO"
    podman exec backend rm -f /data/respaldo_tmp.db
    chmod 600 "$DESTINO"
    echo "Respaldo creado: $DESTINO"
    # Borra los más antiguos y deja los últimos $MANTENER
    ls -1t "$DIR"/contrataciones-*.db | tail -n +$((MANTENER + 1)) | xargs -r rm -f
    ;;
esac
