import itertools

_n = itertools.count(1)


def candidato(**extra):
    """Candidato válido con email único en cada llamada."""
    n = next(_n)
    datos = {"nombre": f"Prueba {n}", "email": f"prueba{n}@mail.com",
             "puesto": "Dev", "telefono": "5512345678"}
    datos.update(extra)
    return datos


# ---------- Autenticación ----------
def test_sin_token_es_rechazado(client):
    assert client.get("/candidatos").status_code == 401


def test_login_correcto(client):
    r = client.post("/login", json={"username": "admin", "password": "Admin12345"})
    assert r.status_code == 200
    assert r.json()["rol"] == "admin"


def test_login_con_clave_incorrecta(client):
    r = client.post("/login", json={"username": "admin", "password": "mala-clave"})
    assert r.status_code == 401


def test_bloqueo_tras_cinco_intentos(client):
    for _ in range(5):
        assert client.post("/login", json={"username": "fantasma", "password": "x"}).status_code == 401
    assert client.post("/login", json={"username": "fantasma", "password": "x"}).status_code == 429


# ---------- Validaciones ----------
def test_telefono_debe_tener_10_digitos(client, admin):
    r = client.post("/candidatos", headers=admin, json=candidato(telefono="123"))
    assert r.status_code == 422


def test_email_duplicado(client, admin):
    c = candidato()
    assert client.post("/candidatos", headers=admin, json=c).status_code == 200
    r = client.post("/candidatos", headers=admin, json=candidato(email=c["email"]))
    assert r.status_code == 409


def test_estado_invalido(client, admin):
    nuevo = client.post("/candidatos", headers=admin, json=candidato()).json()
    r = client.patch(f"/candidatos/{nuevo['id']}?estado=inventado", headers=admin)
    assert r.status_code == 400


# ---------- Roles ----------
def test_reclutador_crea_y_cambia_estado(client, reclutador):
    nuevo = client.post("/candidatos", headers=reclutador, json=candidato())
    assert nuevo.status_code == 200
    r = client.patch(f"/candidatos/{nuevo.json()['id']}?estado=contratado", headers=reclutador)
    assert r.status_code == 200
    assert r.json()["estado"] == "contratado"


def test_reclutador_no_puede_eliminar(client, admin, reclutador):
    nuevo = client.post("/candidatos", headers=admin, json=candidato()).json()
    assert client.delete(f"/candidatos/{nuevo['id']}", headers=reclutador).status_code == 403
    assert client.delete(f"/candidatos/{nuevo['id']}", headers=admin).status_code == 200


def test_auditor_solo_lee(client, auditor):
    assert client.get("/candidatos", headers=auditor).status_code == 200
    assert client.post("/candidatos", headers=auditor, json=candidato()).status_code == 403
    assert client.get("/usuarios", headers=auditor).status_code == 403


def test_reclutador_no_ve_usuarios_ni_bitacora(client, reclutador):
    assert client.get("/usuarios", headers=reclutador).status_code == 403
    assert client.get("/bitacora", headers=reclutador).status_code == 403


# ---------- Usuarios ----------
def test_admin_no_puede_quitarse_sus_permisos(client, admin):
    usuarios = client.get("/usuarios", headers=admin).json()
    yo = next(u for u in usuarios if u["username"] == "admin")
    r = client.patch(f"/usuarios/{yo['id']}", headers=admin, json={"rol": "auditor"})
    assert r.status_code == 400


def test_contrasena_corta_es_rechazada(client, admin):
    r = client.post("/usuarios", headers=admin,
                    json={"username": "corta", "password": "123", "rol": "auditor"})
    assert r.status_code == 422


# ---------- Bitácora ----------
def test_bitacora_registra_acciones(client, admin, auditor):
    client.post("/candidatos", headers=admin, json=candidato(nombre="Registrado en bitacora"))
    r = client.get("/bitacora", headers=auditor)
    assert r.status_code == 200
    acciones = {b["accion"] for b in r.json()}
    assert {"login", "candidato_creado"} <= acciones
