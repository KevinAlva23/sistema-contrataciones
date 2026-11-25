"""Configuración leída del entorno."""

import os

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if len(SECRET_KEY) < 16:
    raise RuntimeError("Falta SECRET_KEY (mínimo 16 caracteres). Genera una: openssl rand -hex 32")

DB_PATH = os.environ.get("DB_PATH", "/data/contrataciones.db")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
DEMO_DATA = os.environ.get("DEMO_DATA", "0") == "1"

TOKEN_HORAS = 8
MAX_INTENTOS = 5
BLOQUEO_MIN = 10
RETENCION_DIAS = 730
DIAS_SIN_AVANCE = 7

ROLES = ("admin", "reclutador", "auditor")
ETAPAS = ["nuevo", "revision", "entrevista", "tecnica", "oferta", "contratado", "rechazado"]
TRANSICIONES: dict[str, list[str]] = {
    "nuevo": ["revision", "rechazado"],
    "revision": ["entrevista", "rechazado"],
    "entrevista": ["tecnica", "rechazado"],
    "tecnica": ["oferta", "rechazado"],
    "oferta": ["contratado", "rechazado"],
    "contratado": [],
    "rechazado": [],
}
MOTIVOS = [
    "Perfil no coincide",
    "Salario fuera de rango",
    "Sin disponibilidad",
    "Reprobó prueba técnica",
    "Declinó la oferta",
    "Otro",
]
