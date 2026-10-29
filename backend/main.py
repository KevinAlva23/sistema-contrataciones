import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import SQLModel, Field, Session, create_engine, select

SECRET = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
ROLES = ("admin", "reclutador", "auditor")

# Bloqueo tras intentos fallidos: usuario -> (fallos, bloqueado_hasta)
INTENTOS = {}
MAX_FALLOS = 5
BLOQUEO_MIN = 10


class Candidato(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str
    puesto: str
    telefono: str
    estado: str = "pendiente"


class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    rol: str = "auditor"
    activo: bool = True


class Bitacora(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha: str
    usuario: str
    accion: str
    detalle: str = ""


class Login(SQLModel):
    username: str
    password: str


class NuevoUsuario(SQLModel):
    username: str
    password: str
    rol: str


class CambioUsuario(SQLModel):
    rol: Optional[str] = None
    activo: Optional[bool] = None
    password: Optional[str] = None


engine = create_engine(os.environ.get("DATABASE_URL", "sqlite:////data/contrataciones.db"))
SQLModel.metadata.create_all(engine)


def hashear(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verificar(password: str, hash_guardado: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash_guardado.encode())


def registrar(s, quien, accion, detalle=""):
    """Agrega un registro a la bitácora (se guarda con el commit de la sesión)."""
    s.add(Bitacora(
        fecha=datetime.now(timezone.utc).isoformat(),
        usuario=quien,
        accion=accion,
        detalle=detalle,
    ))


# Primer administrador si todavía no existe ningún usuario
with Session(engine) as s:
    if not s.exec(select(Usuario)).first():
        clave = os.environ.get("ADMIN_PASSWORD")
        if clave:
            s.add(Usuario(
                username=os.environ.get("ADMIN_USER", "admin"),
                password_hash=hashear(clave),
                rol="admin",
            ))
            s.commit()
        else:
            print("AVISO: no hay usuarios y falta ADMIN_PASSWORD en el entorno")


app = FastAPI(title="Sistema de Contrataciones", root_path="/api")
bearer = HTTPBearer(auto_error=False)


def usuario_actual(cred: HTTPAuthorizationCredentials = Depends(bearer)):
    if not cred:
        raise HTTPException(401, "No autenticado")
    try:
        datos = jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Sesión inválida o expirada")
    with Session(engine) as s:
        u = s.get(Usuario, int(datos["sub"]))
        if not u or not u.activo:
            raise HTTPException(401, "Usuario no válido")
        return u


def requiere(*roles):
    def comprobar(u: Usuario = Depends(usuario_actual)):
        if u.rol not in roles:
            raise HTTPException(403, "No tienes permiso para esta acción")
        return u
    return comprobar


def validar(c, s, id_actual=None):
    if not (c.telefono.isdigit() and len(c.telefono) == 10):
        raise HTTPException(422, "El teléfono debe tener 10 dígitos")
    existente = s.exec(select(Candidato).where(Candidato.email == c.email)).first()
    if existente and existente.id != id_actual:
        raise HTTPException(409, "Ese email ya está registrado")


# ---------- Sesión ----------
@app.post("/login")
def login(datos: Login):
    ahora = datetime.now(timezone.utc)
    fallos, hasta = INTENTOS.get(datos.username, (0, None))
    if hasta and ahora < hasta:
        raise HTTPException(429, "Demasiados intentos. Espera unos minutos.")
    with Session(engine) as s:
        u = s.exec(select(Usuario).where(Usuario.username == datos.username)).first()
        if not u or not u.activo or not verificar(datos.password, u.password_hash):
            fallos += 1
            hasta = ahora + timedelta(minutes=BLOQUEO_MIN) if fallos >= MAX_FALLOS else None
            INTENTOS[datos.username] = (0 if hasta else fallos, hasta)
            detalle = "Cuenta bloqueada 10 min" if hasta else f"Intento fallido {fallos}"
            registrar(s, datos.username[:50], "login_fallido", detalle)
            s.commit()
            raise HTTPException(401, "Usuario o contraseña incorrectos")
        INTENTOS.pop(datos.username, None)
        registrar(s, u.username, "login", "Inicio de sesión")
        s.commit()
        token = jwt.encode(
            {"sub": str(u.id), "exp": ahora + timedelta(hours=8)},
            SECRET,
            algorithm="HS256",
        )
        return {"token": token, "username": u.username, "rol": u.rol}


@app.get("/yo")
def yo(u: Usuario = Depends(usuario_actual)):
    return {"username": u.username, "rol": u.rol}


# ---------- Bitácora (admin y auditor) ----------
@app.get("/bitacora")
def ver_bitacora(limite: int = 300, _: Usuario = Depends(requiere("admin", "auditor"))):
    limite = max(1, min(limite, 1000))
    with Session(engine) as s:
        filas = s.exec(select(Bitacora).order_by(Bitacora.id.desc()).limit(limite)).all()
        return [
            {"id": b.id, "fecha": b.fecha, "usuario": b.usuario,
             "accion": b.accion, "detalle": b.detalle}
            for b in filas
        ]


# ---------- Usuarios (solo admin) ----------
@app.get("/usuarios")
def listar_usuarios(_: Usuario = Depends(requiere("admin"))):
    with Session(engine) as s:
        return [
            {"id": u.id, "username": u.username, "rol": u.rol, "activo": u.activo}
            for u in s.exec(select(Usuario)).all()
        ]


@app.post("/usuarios")
def crear_usuario(datos: NuevoUsuario, yo: Usuario = Depends(requiere("admin"))):
    if datos.rol not in ROLES:
        raise HTTPException(422, "Rol inválido")
    if len(datos.password) < 8:
        raise HTTPException(422, "La contraseña debe tener al menos 8 caracteres")
    with Session(engine) as s:
        if s.exec(select(Usuario).where(Usuario.username == datos.username)).first():
            raise HTTPException(409, "Ese usuario ya existe")
        u = Usuario(
            username=datos.username,
            password_hash=hashear(datos.password),
            rol=datos.rol,
        )
        s.add(u)
        registrar(s, yo.username, "usuario_creado", f"{datos.username} ({datos.rol})")
        s.commit()
        s.refresh(u)
        return {"id": u.id, "username": u.username, "rol": u.rol}


@app.patch("/usuarios/{id}")
def actualizar_usuario(
    id: int, datos: CambioUsuario, yo: Usuario = Depends(requiere("admin"))
):
    with Session(engine) as s:
        u = s.get(Usuario, id)
        if not u:
            raise HTTPException(404, "No encontrado")
        if datos.rol is not None and datos.rol not in ROLES:
            raise HTTPException(422, "Rol inválido")
        if datos.password is not None and len(datos.password) < 8:
            raise HTTPException(422, "La contraseña debe tener al menos 8 caracteres")

        # No te quites tus permisos ni dejes el sistema sin administrador
        pierde_admin = u.rol == "admin" and (
            datos.activo is False or (datos.rol is not None and datos.rol != "admin")
        )
        if pierde_admin:
            if id == yo.id:
                raise HTTPException(400, "No puedes quitarte tus propios permisos")
            admins = s.exec(
                select(Usuario).where(Usuario.rol == "admin", Usuario.activo == True)
            ).all()
            if len(admins) <= 1:
                raise HTTPException(400, "Debe quedar al menos un administrador activo")

        cambios = []
        if datos.rol is not None and datos.rol != u.rol:
            cambios.append(f"rol: {u.rol} -> {datos.rol}")
            u.rol = datos.rol
        if datos.activo is not None and datos.activo != u.activo:
            cambios.append("activado" if datos.activo else "desactivado")
            u.activo = datos.activo
        if datos.password is not None:
            cambios.append("contraseña restablecida")
            u.password_hash = hashear(datos.password)
            INTENTOS.pop(u.username, None)
        s.add(u)
        if cambios:
            registrar(s, yo.username, "usuario_modificado", f"{u.username}: " + ", ".join(cambios))
        s.commit()
        return {"id": u.id, "username": u.username, "rol": u.rol, "activo": u.activo}


@app.delete("/usuarios/{id}")
def borrar_usuario(id: int, yo: Usuario = Depends(requiere("admin"))):
    if id == yo.id:
        raise HTTPException(400, "No puedes eliminar tu propia cuenta")
    with Session(engine) as s:
        u = s.get(Usuario, id)
        if not u:
            raise HTTPException(404, "No encontrado")
        registrar(s, yo.username, "usuario_eliminado", u.username)
        s.delete(u)
        s.commit()
        return {"ok": True}


# ---------- Candidatos ----------
@app.get("/candidatos")
def listar(_: Usuario = Depends(requiere("admin", "reclutador", "auditor"))):
    with Session(engine) as s:
        return s.exec(select(Candidato)).all()


@app.post("/candidatos")
def crear(c: Candidato, yo: Usuario = Depends(requiere("admin", "reclutador"))):
    with Session(engine) as s:
        validar(c, s)
        s.add(c)
        s.commit()
        s.refresh(c)
        registrar(s, yo.username, "candidato_creado", f"{c.nombre} (id {c.id})")
        s.commit()
        s.refresh(c)
        return c


@app.patch("/candidatos/{id}")
def cambiar_estado(
    id: int, estado: str, yo: Usuario = Depends(requiere("admin", "reclutador"))
):
    if estado not in ("pendiente", "contratado", "rechazado"):
        raise HTTPException(400, "Estado inválido")
    with Session(engine) as s:
        c = s.get(Candidato, id)
        if not c:
            raise HTTPException(404, "No encontrado")
        anterior = c.estado
        c.estado = estado
        s.add(c)
        registrar(s, yo.username, "estado_cambiado", f"{c.nombre}: {anterior} -> {estado}")
        s.commit()
        s.refresh(c)
        return c


@app.put("/candidatos/{id}")
def editar(
    id: int, datos: Candidato, yo: Usuario = Depends(requiere("admin", "reclutador"))
):
    with Session(engine) as s:
        c = s.get(Candidato, id)
        if not c:
            raise HTTPException(404, "No encontrado")
        validar(datos, s, id)
        c.nombre = datos.nombre
        c.email = datos.email
        c.puesto = datos.puesto
        c.telefono = datos.telefono
        s.add(c)
        registrar(s, yo.username, "candidato_editado", f"{c.nombre} (id {c.id})")
        s.commit()
        s.refresh(c)
        return c


@app.delete("/candidatos/{id}")
def borrar(id: int, yo: Usuario = Depends(requiere("admin"))):
    with Session(engine) as s:
        c = s.get(Candidato, id)
        if not c:
            raise HTTPException(404, "No encontrado")
        registrar(s, yo.username, "candidato_eliminado", f"{c.nombre} (id {c.id})")
        s.delete(c)
        s.commit()
        return {"ok": True}
