"""API del Sistema de Contrataciones."""

import csv
import io
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import ValidationError
from sqlmodel import Session, SQLModel, col, select

from . import config as cfg
from .db import engine
from .models import (
    AvanzarIn,
    Bitacora,
    Candidato,
    CandidatoEdit,
    CandidatoIn,
    ClaveIn,
    LoginIn,
    Usuario,
    UsuarioEdit,
    UsuarioIn,
    UsuarioOut,
    Vacante,
    VacanteEdit,
    VacanteIn,
    ahora,
)
from .security import (
    HASH_FALSO,
    Actual,
    Admin,
    Audita,
    Edita,
    Sesion,
    crear_token,
    hash_clave,
    validar_clave,
    verificar,
)

INTENTOS: dict[str, list[float]] = {}


def reg(s: Session, quien: str, accion: str, c: Candidato | None = None) -> None:
    s.add(Bitacora(usuario=quien, accion=accion, candidato_id=c.id if c else None))


def _clave_ok(clave: str) -> None:
    try:
        validar_clave(clave)
    except ValueError as e:
        raise HTTPException(422, str(e)) from None


def _bloqueado(k: str) -> bool:
    t = time.time()
    INTENTOS[k] = [x for x in INTENTOS.get(k, []) if t - x < cfg.BLOQUEO_MIN * 60]
    return len(INTENTOS[k]) >= cfg.MAX_INTENTOS


def inicializar() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        if s.exec(select(Usuario)).first() is None:
            if not cfg.ADMIN_PASSWORD:
                raise RuntimeError("Define ADMIN_PASSWORD para crear el primer administrador")
            validar_clave(cfg.ADMIN_PASSWORD)
            s.add(
                Usuario(
                    usuario=cfg.ADMIN_USER,
                    nombre="Administrador",
                    rol="admin",
                    clave_hash=hash_clave(cfg.ADMIN_PASSWORD),
                )
            )
        if cfg.DEMO_DATA and s.exec(select(Vacante)).first() is None:
            _demo(s)
        s.commit()


def _demo(s: Session) -> None:
    vs = [
        Vacante(titulo=t, area=a)
        for t, a in [
            ("Desarrollador/a backend", "Tecnología"),
            ("Analista de RH", "Personas"),
            ("Diseñador/a UX", "Producto"),
        ]
    ]
    s.add_all(vs)
    s.commit()
    datos = [
        ("Ana Torres", "revision", 4, 0, 9),
        ("Luis Méndez", "entrevista", 3, 0, 6),
        ("Sofía Ramírez", "tecnica", 5, 2, 4),
        ("Diego Herrera", "oferta", 5, 0, 3),
        ("Paola Cruz", "nuevo", 0, 1, 1),
        ("Marco Salas", "contratado", 4, 1, 15),
    ]
    for i, (n, est, ev, v, dias) in enumerate(datos):
        f = ahora() - timedelta(days=dias)
        s.add(
            Candidato(
                nombre=n,
                email=f"{n.split()[0].lower()}@ejemplo.mx",
                telefono=f"55{10000000 + i * 1111111}",
                vacante_id=vs[v].id or 0,
                estado=est,
                evaluacion=ev,
                creado=f,
                actualizado=f,
                salario=42000 if est in ("oferta", "contratado") else 0,
                oferta_solicitada=est in ("oferta", "contratado"),
                oferta_aprobada=est == "contratado",
            )
        )


@asynccontextmanager
async def ciclo(_: FastAPI) -> AsyncIterator[None]:
    inicializar()
    yield


app = FastAPI(
    title="Sistema de Contrataciones",
    version="2.0",
    lifespan=ciclo,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)
api = APIRouter(prefix="/api")


@api.get("/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok"}


@api.get("/config")
def configuracion() -> dict[str, Any]:
    return {
        "etapas": cfg.ETAPAS,
        "transiciones": cfg.TRANSICIONES,
        "motivos": cfg.MOTIVOS,
        "roles": cfg.ROLES,
    }


# ---------- Sesión ----------
@api.post("/login")
def login(d: LoginIn, req: Request, s: Sesion) -> dict[str, Any]:
    ip = req.headers.get("x-real-ip") or (req.client.host if req.client else "?")
    k = f"{d.usuario.lower()}|{ip}"
    if _bloqueado(k):
        raise HTTPException(429, f"Demasiados intentos. Espera {cfg.BLOQUEO_MIN} minutos.")
    u = s.exec(select(Usuario).where(col(Usuario.usuario) == d.usuario)).first()
    valido = verificar(d.clave, u.clave_hash if u else HASH_FALSO)
    if u is None or not u.activo or not valido:
        INTENTOS.setdefault(k, []).append(time.time())
        reg(s, d.usuario, "Intento de acceso fallido")
        s.commit()
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    INTENTOS.pop(k, None)
    reg(s, u.usuario, "Inicio de sesión")
    s.commit()
    return {"token": crear_token(u), "usuario": UsuarioOut.model_validate(u)}


@api.get("/yo", response_model=UsuarioOut)
def yo(u: Actual) -> Usuario:
    return u


@api.post("/cambiar-clave")
def cambiar_clave(d: ClaveIn, s: Sesion, u: Actual) -> dict[str, str]:
    if not verificar(d.actual, u.clave_hash):
        raise HTTPException(400, "La contraseña actual no es correcta")
    _clave_ok(d.nueva)
    u.clave_hash = hash_clave(d.nueva)
    u.version_token += 1
    reg(s, u.usuario, "Cambio de contraseña")
    s.commit()
    return {"token": crear_token(u)}


# ---------- Usuarios ----------
def _otro_admin(s: Session, u: Usuario) -> bool:
    q = select(Usuario).where(
        col(Usuario.rol) == "admin",
        col(Usuario.activo) == True,  # noqa: E712
        col(Usuario.id) != u.id,
    )
    return s.exec(q).first() is not None


def _usuario(s: Session, uid: int) -> Usuario:
    u = s.get(Usuario, uid)
    if u is None:
        raise HTTPException(404, "Usuario no encontrado")
    return u


@api.get("/usuarios", response_model=list[UsuarioOut])
def usuarios(s: Sesion, _: Admin) -> list[Usuario]:
    return list(s.exec(select(Usuario).order_by(col(Usuario.id))).all())


@api.post("/usuarios", response_model=UsuarioOut, status_code=201)
def crear_usuario(d: UsuarioIn, s: Sesion, a: Admin) -> Usuario:
    if d.rol not in cfg.ROLES:
        raise HTTPException(422, "Rol no válido")
    _clave_ok(d.clave)
    if s.exec(select(Usuario).where(col(Usuario.usuario) == d.usuario)).first():
        raise HTTPException(409, "Ese usuario ya existe")
    u = Usuario(usuario=d.usuario, nombre=d.nombre, rol=d.rol, clave_hash=hash_clave(d.clave))
    s.add(u)
    reg(s, a.usuario, f"Usuario creado: {d.usuario} ({d.rol})")
    s.commit()
    s.refresh(u)
    return u


@api.patch("/usuarios/{uid}", response_model=UsuarioOut)
def editar_usuario(uid: int, d: UsuarioEdit, s: Sesion, a: Admin) -> Usuario:
    u = _usuario(s, uid)
    cambios = d.model_dump(exclude_unset=True)
    if "rol" in cambios and cambios["rol"] not in cfg.ROLES:
        raise HTTPException(422, "Rol no válido")
    quita_admin = u.rol == "admin" and (
        cambios.get("rol", "admin") != "admin" or cambios.get("activo") is False
    )
    if quita_admin and not _otro_admin(s, u):
        raise HTTPException(409, "Debe existir al menos un administrador activo")
    if cambios.get("clave"):
        _clave_ok(cambios["clave"])
        u.clave_hash = hash_clave(cambios.pop("clave"))
        u.version_token += 1
    cambios.pop("clave", None)
    for k, v in cambios.items():
        if v is not None:
            setattr(u, k, v)
    if cambios.get("activo") is False:
        u.version_token += 1
    reg(s, a.usuario, f"Usuario modificado: {u.usuario}")
    s.commit()
    s.refresh(u)
    return u


@api.post("/usuarios/{uid}/cerrar-sesiones")
def cerrar_sesiones(uid: int, s: Sesion, a: Admin) -> dict[str, str]:
    u = _usuario(s, uid)
    u.version_token += 1
    reg(s, a.usuario, f"Sesiones revocadas: {u.usuario}")
    s.commit()
    return {"estado": "ok"}


@api.delete("/usuarios/{uid}", status_code=204)
def eliminar_usuario(uid: int, s: Sesion, a: Admin) -> None:
    u = _usuario(s, uid)
    if u.id == a.id:
        raise HTTPException(409, "No puedes eliminar tu propia cuenta")
    if u.rol == "admin" and not _otro_admin(s, u):
        raise HTTPException(409, "Debe existir al menos un administrador activo")
    s.delete(u)
    reg(s, a.usuario, f"Usuario eliminado: {u.usuario}")
    s.commit()


# ---------- Vacantes ----------
@api.get("/vacantes", response_model=list[Vacante])
def vacantes(s: Sesion, _: Actual) -> list[Vacante]:
    return list(s.exec(select(Vacante).order_by(col(Vacante.id))).all())


@api.post("/vacantes", response_model=Vacante, status_code=201)
def crear_vacante(d: VacanteIn, s: Sesion, u: Edita) -> Vacante:
    v = Vacante(titulo=d.titulo, area=d.area)
    s.add(v)
    reg(s, u.usuario, f"Vacante creada: {d.titulo}")
    s.commit()
    s.refresh(v)
    return v


@api.patch("/vacantes/{vid}", response_model=Vacante)
def editar_vacante(vid: int, d: VacanteEdit, s: Sesion, u: Edita) -> Vacante:
    v = s.get(Vacante, vid)
    if v is None:
        raise HTTPException(404, "Vacante no encontrada")
    for k, val in d.model_dump(exclude_unset=True).items():
        if val is not None:
            setattr(v, k, val)
    reg(s, u.usuario, f"Vacante modificada: {v.titulo}")
    s.commit()
    s.refresh(v)
    return v


# ---------- Candidatos ----------
def _cand(s: Session, cid: int) -> Candidato:
    c = s.get(Candidato, cid)
    if c is None:
        raise HTTPException(404, "Candidato no encontrado")
    return c


def _correo_libre(s: Session, email: str, excepto: int | None = None) -> None:
    c = s.exec(select(Candidato).where(col(Candidato.email) == email)).first()
    if c is not None and c.id != excepto:
        raise HTTPException(409, "Ya existe un candidato con ese correo")


def _vacante(s: Session, vid: int, abierta: bool = False) -> Vacante:
    v = s.get(Vacante, vid)
    if v is None or (abierta and not v.abierta):
        raise HTTPException(422, "La vacante no existe o está cerrada")
    return v


@api.get("/candidatos/exportar")
def exportar(s: Sesion, u: Audita) -> Response:
    vs = {v.id: v.titulo for v in s.exec(select(Vacante)).all()}
    buf = io.StringIO()
    w = csv.writer(buf, quoting=csv.QUOTE_ALL)
    w.writerow(["nombre", "email", "telefono", "vacante", "estado", "evaluacion", "registro"])
    for c in s.exec(select(Candidato).order_by(col(Candidato.id))).all():
        fila = [
            c.nombre,
            c.email,
            c.telefono,
            vs.get(c.vacante_id, ""),
            c.estado,
            c.evaluacion,
            c.creado.date().isoformat(),
        ]
        w.writerow(
            [f"'{x}" if isinstance(x, str) and x[:1] in "=+-@\t\r" and x else x for x in fila]
        )
    reg(s, u.usuario, "Exportación CSV")
    s.commit()
    return Response(
        buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=candidatos.csv"},
    )


@api.post("/candidatos/importar")
async def importar(archivo: UploadFile, s: Sesion, u: Admin) -> dict[str, Any]:
    datos = await archivo.read(1_000_001)
    if len(datos) > 1_000_000:
        raise HTTPException(413, "El archivo supera 1 MB")
    try:
        filas = list(csv.DictReader(io.StringIO(datos.decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error):
        raise HTTPException(400, "El archivo debe ser un CSV en UTF-8") from None
    vs = {v.titulo.lower(): v.id for v in s.exec(select(Vacante)).all()}
    vistos: set[str] = set()
    errores: list[dict[str, Any]] = []
    ok = 0
    for n, f in enumerate(filas, start=2):
        try:
            vid = vs.get((f.get("vacante") or "").strip().lower())
            if vid is None:
                raise ValueError("Vacante no encontrada")
            d = CandidatoIn(
                nombre=f.get("nombre") or "",
                email=f.get("email") or "",
                telefono=f.get("telefono") or "",
                vacante_id=vid,
                aviso_privacidad=(f.get("aviso") or "").strip().lower() in ("si", "sí"),
            )
            if not d.aviso_privacidad:
                raise ValueError("Falta la confirmación del aviso de privacidad (aviso = si)")
            if (
                d.email in vistos
                or s.exec(select(Candidato).where(col(Candidato.email) == d.email)).first()
            ):
                raise ValueError("Correo duplicado")
        except (ValidationError, ValueError):
            errores.append({"fila": n, "motivo": "Fila no válida"})
            continue
        vistos.add(d.email)
        c = Candidato(nombre=d.nombre, email=d.email, telefono=d.telefono, vacante_id=vid)
        s.add(c)
        ok += 1
    reg(s, u.usuario, f"Importación CSV: {ok} candidatos, {len(errores)} con error")
    s.commit()
    return {"importados": ok, "errores": errores}


@api.get("/candidatos", response_model=list[Candidato])
def candidatos(
    s: Sesion, _: Actual, q: str = "", estado: str = "", vacante_id: int = 0
) -> list[Candidato]:
    sel = select(Candidato).order_by(col(Candidato.actualizado).desc())
    if estado:
        sel = sel.where(col(Candidato.estado) == estado)
    if vacante_id:
        sel = sel.where(col(Candidato.vacante_id) == vacante_id)
    if q:
        like = f"%{q.strip()}%"
        sel = sel.where(col(Candidato.nombre).ilike(like) | col(Candidato.email).ilike(like))
    return list(s.exec(sel).all())


@api.post("/candidatos", response_model=Candidato, status_code=201)
def crear_candidato(d: CandidatoIn, s: Sesion, u: Edita) -> Candidato:
    if not d.aviso_privacidad:
        raise HTTPException(422, "Se requiere la aceptación del aviso de privacidad")
    _vacante(s, d.vacante_id, abierta=True)
    _correo_libre(s, d.email)
    c = Candidato(nombre=d.nombre, email=d.email, telefono=d.telefono, vacante_id=d.vacante_id)
    s.add(c)
    s.flush()
    reg(s, u.usuario, f"Registro de candidato: {c.nombre}", c)
    s.commit()
    s.refresh(c)
    return c


@api.patch("/candidatos/{cid}", response_model=Candidato)
def editar_candidato(cid: int, d: CandidatoEdit, s: Sesion, u: Edita) -> Candidato:
    c = _cand(s, cid)
    cambios = {k: v for k, v in d.model_dump(exclude_unset=True).items() if v is not None}
    if "email" in cambios:
        _correo_libre(s, cambios["email"], c.id)
    if "vacante_id" in cambios:
        _vacante(s, cambios["vacante_id"])
    if "salario" in cambios and c.oferta_aprobada:
        raise HTTPException(409, "La oferta ya fue aprobada; el salario no puede cambiar")
    for k, v in cambios.items():
        setattr(c, k, v)
    c.actualizado = ahora()
    reg(s, u.usuario, "Datos actualizados: " + ", ".join(sorted(cambios)), c)
    s.commit()
    s.refresh(c)
    return c


@api.post("/candidatos/{cid}/avanzar", response_model=Candidato)
def avanzar(cid: int, d: AvanzarIn, s: Sesion, u: Edita) -> Candidato:
    c = _cand(s, cid)
    if d.estado not in cfg.TRANSICIONES.get(c.estado, []):
        raise HTTPException(409, f"Transición no permitida: {c.estado} → {d.estado}")
    if d.estado == "rechazado":
        if d.motivo not in cfg.MOTIVOS:
            raise HTTPException(422, "Selecciona un motivo de rechazo válido")
        c.motivo_rechazo = d.motivo
    if d.estado == "contratado" and not c.oferta_aprobada:
        raise HTTPException(409, "La oferta debe estar aprobada para contratar")
    anterior, c.estado, c.actualizado = c.estado, d.estado, ahora()
    reg(s, u.usuario, f"{anterior} → {d.estado}" + (f" ({d.motivo})" if d.motivo else ""), c)
    s.commit()
    s.refresh(c)
    return c


@api.post("/candidatos/{cid}/solicitar-oferta", response_model=Candidato)
def solicitar_oferta(cid: int, s: Sesion, u: Edita) -> Candidato:
    c = _cand(s, cid)
    if c.estado != "oferta" or c.salario <= 0 or c.oferta_aprobada:
        raise HTTPException(409, "Requiere etapa Oferta, salario capturado y oferta sin aprobar")
    c.oferta_solicitada, c.actualizado = True, ahora()
    reg(s, u.usuario, f"Aprobación de oferta solicitada (${c.salario})", c)
    s.commit()
    s.refresh(c)
    return c


@api.post("/candidatos/{cid}/aprobar-oferta", response_model=Candidato)
def aprobar_oferta(cid: int, s: Sesion, u: Admin) -> Candidato:
    c = _cand(s, cid)
    if not c.oferta_solicitada or c.oferta_aprobada:
        raise HTTPException(409, "No hay una oferta pendiente de aprobación")
    c.oferta_aprobada, c.actualizado = True, ahora()
    reg(s, u.usuario, f"Oferta aprobada (${c.salario})", c)
    s.commit()
    s.refresh(c)
    return c


@api.get("/candidatos/{cid}/historial", response_model=list[Bitacora])
def historial(cid: int, s: Sesion, _: Actual) -> list[Bitacora]:
    q = select(Bitacora).where(col(Bitacora.candidato_id) == cid).order_by(col(Bitacora.id).desc())
    return list(s.exec(q).all())


@api.delete("/candidatos/{cid}", status_code=204)
def eliminar_candidato(cid: int, s: Sesion, u: Admin) -> None:
    c = _cand(s, cid)
    s.delete(c)
    reg(s, u.usuario, f"Candidato eliminado: {c.nombre}")
    s.commit()


# ---------- Auditoría ----------
@api.get("/bitacora", response_model=list[Bitacora])
def bitacora(s: Sesion, _: Audita, limite: int = 200) -> list[Bitacora]:
    q = select(Bitacora).order_by(col(Bitacora.id).desc()).limit(min(max(limite, 1), 1000))
    return list(s.exec(q).all())


@api.get("/estadisticas")
def estadisticas(s: Sesion, _: Audita) -> dict[str, Any]:
    cs = s.exec(select(Candidato)).all()
    vs = {v.id: v.titulo for v in s.exec(select(Vacante)).all()}
    por_estado = dict.fromkeys(cfg.ETAPAS, 0)
    por_vacante: dict[str, int] = {}
    por_mes: dict[str, int] = {}
    limite = ahora() - timedelta(days=cfg.DIAS_SIN_AVANCE)
    sin_avance = 0
    for c in cs:
        por_estado[c.estado] = por_estado.get(c.estado, 0) + 1
        t = vs.get(c.vacante_id, "—")
        por_vacante[t] = por_vacante.get(t, 0) + 1
        m = c.creado.strftime("%Y-%m")
        por_mes[m] = por_mes.get(m, 0) + 1
        if c.estado not in ("contratado", "rechazado") and c.actualizado < limite:
            sin_avance += 1
    cont = por_estado["contratado"]
    return {
        "total": len(cs),
        "por_estado": por_estado,
        "por_vacante": por_vacante,
        "por_mes": dict(sorted(por_mes.items())),
        "sin_avance": sin_avance,
        "conversion": round(cont / len(cs) * 100) if cs else 0,
    }


app.include_router(api)
