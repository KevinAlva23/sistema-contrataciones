import os
import sys
import tempfile

import pytest

# Base temporal y secretos de prueba: se definen ANTES de importar la app
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["SECRET_KEY"] = "clave-solo-para-pruebas"
os.environ["ADMIN_USER"] = "admin"
os.environ["ADMIN_PASSWORD"] = "Admin12345"
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402


def cabecera(client, usuario, clave):
    r = client.post("/login", json={"username": usuario, "password": clave})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="session")
def client():
    return TestClient(main.app)


@pytest.fixture(scope="session")
def admin(client):
    return cabecera(client, "admin", "Admin12345")


@pytest.fixture(scope="session")
def reclutador(client, admin):
    r = client.post("/usuarios", headers=admin,
                    json={"username": "rec", "password": "Reclutador1", "rol": "reclutador"})
    assert r.status_code == 200, r.text
    return cabecera(client, "rec", "Reclutador1")


@pytest.fixture(scope="session")
def auditor(client, admin):
    r = client.post("/usuarios", headers=admin,
                    json={"username": "aud", "password": "Auditor123", "rol": "auditor"})
    assert r.status_code == 200, r.text
    return cabecera(client, "aud", "Auditor123")
