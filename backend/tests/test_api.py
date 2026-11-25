import io

from conftest import candidato, con_rol, entrar


def test_salud(c):
    assert c.get("/api/salud").json() == {"estado": "ok"}


def test_requiere_token(c):
    assert c.get("/api/candidatos").status_code == 401


def test_bloqueo_tras_cinco_fallos(c):
    for _ in range(5):
        assert c.post("/api/login", json={"usuario": "admin", "clave": "mala"}).status_code == 401
    r = c.post("/api/login", json={"usuario": "admin", "clave": "ClaveAdmin123"})
    assert r.status_code == 429


def test_roles(c):
    adm = entrar(c)
    rec, aud = con_rol(c, "reclutador"), con_rol(c, "auditor")
    cand = candidato(c, rec)
    assert c.get("/api/bitacora", headers=rec).status_code == 403
    assert c.get("/api/bitacora", headers=aud).status_code == 200
    assert c.post("/api/candidatos", headers=aud, json={}).status_code == 403
    assert c.delete(f"/api/candidatos/{cand['id']}", headers=rec).status_code == 403
    assert c.get("/api/usuarios", headers=rec).status_code == 403
    assert c.get("/api/candidatos/exportar", headers=aud).status_code == 200
    assert c.delete(f"/api/candidatos/{cand['id']}", headers=adm).status_code == 204


def test_validaciones(c):
    h = entrar(c)
    base = candidato(c, h)
    vid = base["vacante_id"]
    ok = {
        "nombre": "X",
        "email": "x@ej.mx",
        "telefono": "5512345678",
        "vacante_id": vid,
        "aviso_privacidad": True,
    }
    assert c.post("/api/candidatos", headers=h, json={**ok, "telefono": "123"}).status_code == 422
    assert c.post("/api/candidatos", headers=h, json={**ok, "email": "malo"}).status_code == 422
    assert (
        c.post("/api/candidatos", headers=h, json={**ok, "aviso_privacidad": False}).status_code
        == 422
    )
    assert (
        c.post("/api/candidatos", headers=h, json={**ok, "email": "ANA@ejemplo.mx"}).status_code
        == 409
    )


def test_cliente_no_controla_estado(c):
    h = entrar(c)
    assert candidato(c, h, estado="contratado", id=99)["estado"] == "nuevo"


def test_flujo_completo_con_aprobacion(c):
    adm = entrar(c)
    rec = con_rol(c, "reclutador")
    cid = candidato(c, rec)["id"]
    ir = lambda est, **k: c.post(
        f"/api/candidatos/{cid}/avanzar", headers=rec, json={"estado": est, **k}
    )  # noqa: E731
    assert ir("oferta").status_code == 409
    for est in ("revision", "entrevista", "tecnica", "oferta"):
        assert ir(est).status_code == 200
    assert ir("contratado").status_code == 409
    assert c.post(f"/api/candidatos/{cid}/solicitar-oferta", headers=rec).status_code == 409
    assert (
        c.patch(f"/api/candidatos/{cid}", headers=rec, json={"salario": 40000}).status_code == 200
    )
    assert c.post(f"/api/candidatos/{cid}/solicitar-oferta", headers=rec).status_code == 200
    assert c.post(f"/api/candidatos/{cid}/aprobar-oferta", headers=rec).status_code == 403
    assert c.post(f"/api/candidatos/{cid}/aprobar-oferta", headers=adm).status_code == 200
    assert ir("contratado").json()["estado"] == "contratado"
    assert len(c.get(f"/api/candidatos/{cid}/historial", headers=rec).json()) >= 7


def test_rechazo_requiere_motivo(c):
    h = entrar(c)
    cid = candidato(c, h)["id"]
    url = f"/api/candidatos/{cid}/avanzar"
    assert c.post(url, headers=h, json={"estado": "rechazado"}).status_code == 422
    r = c.post(url, headers=h, json={"estado": "rechazado", "motivo": "Sin disponibilidad"})
    assert r.json()["motivo_rechazo"] == "Sin disponibilidad"
    assert c.post(url, headers=h, json={"estado": "revision"}).status_code == 409


def test_exportar_neutraliza_formulas(c):
    h = entrar(c)
    candidato(c, h, nombre="=CMD()")
    assert "'=CMD()" in c.get("/api/candidatos/exportar", headers=h).text


def test_cambiar_clave_revoca_sesion_anterior(c):
    h = entrar(c)
    r = c.post(
        "/api/cambiar-clave", headers=h, json={"actual": "ClaveAdmin123", "nueva": "NuevaClave99x"}
    )
    assert r.status_code == 200
    assert c.get("/api/yo", headers=h).status_code == 401
    nuevo = {"Authorization": f"Bearer {r.json()['token']}"}
    assert c.get("/api/yo", headers=nuevo).status_code == 200


def test_politica_de_clave(c):
    h = entrar(c)
    r = c.post(
        "/api/usuarios",
        headers=h,
        json={"usuario": "u1", "nombre": "U", "rol": "auditor", "clave": "corta"},
    )
    assert r.status_code == 422


def test_ultimo_admin_protegido(c):
    h = entrar(c)
    uid = c.get("/api/yo", headers=h).json()["id"]
    assert c.patch(f"/api/usuarios/{uid}", headers=h, json={"rol": "auditor"}).status_code == 409
    assert c.delete(f"/api/usuarios/{uid}", headers=h).status_code == 409


def test_importar_csv(c):
    h = entrar(c)
    candidato(c, h)
    csv_ = (
        "nombre,email,telefono,vacante,aviso\n"
        "Luis,luis@ej.mx,5511111111,Dev,si\n"
        "Mal,mal@ej.mx,123,Dev,si\n"
        "Dup,ana@ejemplo.mx,5522222222,Dev,si\n"
    )
    r = c.post(
        "/api/candidatos/importar",
        headers=h,
        files={"archivo": ("c.csv", io.BytesIO(csv_.encode()), "text/csv")},
    )
    assert r.json()["importados"] == 1
    assert [e["fila"] for e in r.json()["errores"]] == [3, 4]
