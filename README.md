# Talento · Sistema de Contrataciones (v2)

Vue 3 + FastAPI + SQLite, en contenedores (Podman o Docker).

## Proceso de contratación
Nuevo → Revisión de CV → Entrevista → Prueba técnica → Oferta → Contratado (o Rechazado con motivo).
Las transiciones se validan en el servidor. Contratar exige una **oferta aprobada** por un administrador.

## Arrancar
```bash
./iniciar.sh            # crea .env la primera vez, construye y levanta
# http://localhost:8080   ·   API: http://localhost:8080/api/docs
./iniciar.sh detener
```

## Desarrollo local
```bash
make instalar
make dev-api   # terminal 1 (usuario admin / Admin12345x, con datos de ejemplo)
make dev-web   # terminal 2 -> http://localhost:5173
make pruebas lint
```

## Respaldos
`./respaldo.sh` · `./respaldo.sh listar` · `./respaldo.sh restaurar ARCHIVO`.
Define `RESPALDO_DESTINO` en `.env` para copiar cada respaldo fuera del equipo (rsync).

## Análisis estático (GitHub Actions)
- **CI**: ruff, mypy, bandit, pip-audit, pytest (backend); eslint, build, npm audit (frontend).
- **Seguridad**: CodeQL, gitleaks (secretos), Trivy (dependencias y Dockerfiles/compose). Dependabot semanal.
