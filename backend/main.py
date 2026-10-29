import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import SQLModel, Field, Session, create_engine, select

# Clave para firmar los tokens. Si no se define, se genera una al azar
# (las sesiones se cierran al reiniciar el backend).
SECRET = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
ROLES = ("admin", "reclutador", "auditor")
INTENTOS = {}  # username -> (fallos, bloqueado_hasta)
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
    rol: str = "consulta"
    activo: bool = True


class Login(SQLModel):
    username: str
    password: str


class NuevoUsuario(SQLModel):
    username: str
    password: str
    rol: str


engine = create_engine("sqlite:////data/contrataciones.db")
SQLModel.metadata.create_all(engine)


def hashear(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verificar(password: str, hash_guardado: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash_guardado.encode())


# Crea el primer administrador si todavía no existe ningún usuario
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
            raise HTTPException(401, "Usuario o contraseña incorrectos")
        INTENTOS.pop(datos.username, None)
        token = jwt.encode(
            {"sub": str(u.id), "exp": ahora + timedelta(hours=8)},
            SECRET,
            algorithm="HS256",
        )
        return {"token": token, "username": u.username, "rol": u.rol}
# ---------- Usuarios (solo admin) ----------
@app.get("/usuarios")
def listar_usuarios(_: Usuario = Depends(requiere("admin"))):
    with Session(engine) as s:
        return [
            {"id": u.id, "username": u.username, "rol": u.rol, "activo": u.activo}
            for u in s.exec(select(Usuario)).all()
        ]


@app.post("/usuarios")
def crear_usuario(datos: NuevoUsuario, _: Usuario = Depends(requiere("admin"))):
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
        s.commit()
        s.refresh(u)
        return {"id": u.id, "username": u.username, "rol": u.rol}


@app.delete("/usuarios/{id}")
def borrar_usuario(id: int, yo: Usuario = Depends(requiere("admin"))):
    if id == yo.id:
        raise HTTPException(400, "No puedes eliminar tu propia cuenta")
    with Session(engine) as s:
        u = s.get(Usuario, id)
        if not u:
            raise HTTPException(404, "No encontrado")
        s.delete(u)
        s.commit()
        return {"ok": True}


# ---------- Candidatos ----------
@app.get("/candidatos")
def listar(_: Usuario = Depends(requiere("admin", "reclutador", "auditor"))):
    with Session(engine) as s:
        return s.exec(select(Candidato)).all()


@app.post("/candidatos")
def crear(c: Candidato, _: Usuario = Depends(requiere("admin", "reclutador"))):
    with Session(engine) as s:
        validar(c, s)
        s.add(c)
        s.commit()
        s.refresh(c)
        return c


@app.patch("/candidatos/{id}")
def cambiar_estado(
    id: int, estado: str, _: Usuario = Depends(requiere("admin", "reclutador"))
):
    if estado not in ("pendiente", "contratado", "rechazado"):
        raise HTTPException(400, "Estado inválido")
    with Session(engine) as s:
        c = s.get(Candidato, id)
        if not c:
            raise HTTPException(404, "No encontrado")
        c.estado = estado
        s.add(c)
        s.commit()
        return c


@app.put("/candidatos/{id}")
def editar(
    id: int, datos: Candidato, _: Usuario = Depends(requiere("admin", "reclutador"))
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
        s.commit()
        s.refresh(c)
        return c


@app.delete("/candidatos/{id}")
def borrar(id: int, _: Usuario = Depends(requiere("admin"))):
    with Session(engine) as s:
        c = s.get(Candidato, id)
        if not c:
            raise HTTPException(404, "No encontrado")
        s.delete(c)
        s.commit()
        return {"ok": True}


class CambioUsuario(SQLModel):
    rol: Optional[str] = None
    activo: Optional[bool] = None
    password: Optional[str] = None


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

        # No te quites tus propios permisos ni dejes el sistema sin administrador
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

        if datos.rol is not None:
            u.rol = datos.rol
        if datos.activo is not None:
            u.activo = datos.activo
        if datos.password is not None:
            u.password_hash = hashear(datos.password)
            globals().get("INTENTOS", {}).pop(u.username, None)
        s.add(u)
        s.commit()
        return {"id": u.id, "username": u.username, "rol": u.rol, "activo": u.activo}
