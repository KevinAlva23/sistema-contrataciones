import os
import secrets
import tempfile
from pathlib import Path

os.environ["SECRET_KEY"] = secrets.token_hex(32)
os.environ["DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test.db")
os.environ["ADMIN_USER"] = "admin"
os.environ["ADMIN_PASSWORD"] = "ClaveAdmin123"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app.db import engine
from app.main import INTENTOS, app, inicializar


@pytest.fixture()
def c() -> TestClient:
    SQLModel.metadata.drop_all(engine)
    INTENTOS.clear()
    inicializar()
    return TestClient(app)


def entrar(c: TestClient, usuario: str = "admin", clave: str = "ClaveAdmin123") -> dict[str, str]:
    r = c.post("/api/login", json={"usuario": usuario, "clave": clave})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def con_rol(c: TestClient, rol: str) -> dict[str, str]:
    h = entrar(c)
    r = c.post(
        "/api/usuarios",
        headers=h,
        json={"usuario": rol, "nombre": rol.title(), "rol": rol, "clave": "Clave12345x"},
    )
    assert r.status_code == 201, r.text
    return entrar(c, rol, "Clave12345x")


def candidato(
    c: TestClient, h: dict[str, str], email: str = "ana@ejemplo.mx", **extra: object
) -> dict:
    vid = c.post("/api/vacantes", headers=h, json={"titulo": "Dev"}).json()["id"]
    cuerpo = {
        "nombre": "Ana Torres",
        "email": email,
        "telefono": "5512345678",
        "vacante_id": vid,
        "aviso_privacidad": True,
        **extra,
    }
    r = c.post("/api/candidatos", headers=h, json=cuerpo)
    assert r.status_code == 201, r.text
    return r.json()
