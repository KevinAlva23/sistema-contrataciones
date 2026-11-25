"""Contraseñas, tokens y dependencias de autorización."""

import re
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from .config import SECRET_KEY, TOKEN_HORAS
from .db import get_session
from .models import Usuario

bearer = HTTPBearer(auto_error=False)
Sesion = Annotated[Session, Depends(get_session)]


def hash_clave(clave: str) -> str:
    return bcrypt.hashpw(clave.encode(), bcrypt.gensalt()).decode()


def verificar(clave: str, hash_: str) -> bool:
    try:
        return bcrypt.checkpw(clave.encode(), hash_.encode())
    except ValueError:
        return False


HASH_FALSO = hash_clave("clave-falsa-para-igualar-tiempos")


def validar_clave(clave: str) -> None:
    if (
        len(clave) < 10
        or not re.search(r"[a-z]", clave)
        or not re.search(r"[A-Z]", clave)
        or not re.search(r"\d", clave)
    ):
        raise ValueError("La contraseña necesita 10+ caracteres, mayúsculas, minúsculas y números")


def crear_token(u: Usuario) -> str:
    exp = datetime.now(UTC) + timedelta(hours=TOKEN_HORAS)
    return jwt.encode({"sub": str(u.id), "tv": u.version_token, "exp": exp}, SECRET_KEY, "HS256")


def usuario_actual(
    cred: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)], s: Sesion
) -> Usuario:
    if cred is None:
        raise HTTPException(401, "No autenticado")
    try:
        datos = jwt.decode(cred.credentials, SECRET_KEY, algorithms=["HS256"])
        u = s.get(Usuario, int(datos["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Sesión inválida o caducada") from None
    if u is None or not u.activo or u.version_token != datos.get("tv"):
        raise HTTPException(401, "Sesión inválida o caducada")
    return u


def requiere(*roles: str) -> Any:
    def dependencia(u: Annotated[Usuario, Depends(usuario_actual)]) -> Usuario:
        if u.rol not in roles:
            raise HTTPException(403, "Tu perfil no tiene permiso para esta acción")
        return u

    return Depends(dependencia)


Actual = Annotated[Usuario, Depends(usuario_actual)]
Admin = Annotated[Usuario, requiere("admin")]
Edita = Annotated[Usuario, requiere("admin", "reclutador")]
Audita = Annotated[Usuario, requiere("admin", "auditor")]
