"""Tablas y esquemas de entrada/salida."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from pydantic import BaseModel, ConfigDict, NaiveDatetime, StringConstraints
from pydantic import Field as PField
from sqlmodel import Field, SQLModel

from .config import RETENCION_DIAS


def ahora() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def conservar_hasta() -> datetime:
    return ahora() + timedelta(days=RETENCION_DIAS)


Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Correo = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, to_lower=True, max_length=120, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    ),
]
Telefono = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{10}$")]
Notas = Annotated[str, StringConstraints(max_length=2000)]
Clave = Annotated[str, StringConstraints(max_length=72)]
Login = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9._-]{3,40}$")]


class Usuario(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    usuario: str = Field(index=True, unique=True)
    nombre: str
    rol: str
    clave_hash: str
    activo: bool = True
    version_token: int = 0
    creado: NaiveDatetime = Field(default_factory=ahora)


class Vacante(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    titulo: str
    area: str = "General"
    abierta: bool = True
    creado: NaiveDatetime = Field(default_factory=ahora)


class Candidato(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(index=True, unique=True)
    telefono: str
    vacante_id: int = Field(foreign_key="vacante.id")
    estado: str = "nuevo"
    evaluacion: int = 0
    notas: str = ""
    salario: int = 0
    oferta_solicitada: bool = False
    oferta_aprobada: bool = False
    motivo_rechazo: str = ""
    creado: NaiveDatetime = Field(default_factory=ahora)
    actualizado: NaiveDatetime = Field(default_factory=ahora)
    conservar_hasta: NaiveDatetime = Field(default_factory=conservar_hasta)


class Bitacora(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    fecha: NaiveDatetime = Field(default_factory=ahora)
    usuario: str
    accion: str
    candidato_id: int | None = Field(default=None, index=True)


class UsuarioOut(SQLModel):
    id: int
    usuario: str
    nombre: str
    rol: str
    activo: bool
    creado: NaiveDatetime


class Entrada(BaseModel):
    model_config = ConfigDict(extra="ignore")


class LoginIn(Entrada):
    usuario: Texto
    clave: Clave


class ClaveIn(Entrada):
    actual: Clave
    nueva: Clave


class UsuarioIn(Entrada):
    usuario: Login
    nombre: Texto
    rol: str
    clave: Clave


class UsuarioEdit(Entrada):
    nombre: Texto | None = None
    rol: str | None = None
    activo: bool | None = None
    clave: Clave | None = None


class VacanteIn(Entrada):
    titulo: Texto
    area: Texto = "General"


class VacanteEdit(Entrada):
    titulo: Texto | None = None
    area: Texto | None = None
    abierta: bool | None = None


class CandidatoIn(Entrada):
    nombre: Texto
    email: Correo
    telefono: Telefono
    vacante_id: int
    aviso_privacidad: bool


class CandidatoEdit(Entrada):
    nombre: Texto | None = None
    email: Correo | None = None
    telefono: Telefono | None = None
    vacante_id: int | None = None
    evaluacion: Annotated[int, PField(ge=0, le=5)] | None = None
    notas: Notas | None = None
    salario: Annotated[int, PField(ge=0, le=10_000_000)] | None = None


class AvanzarIn(Entrada):
    estado: str
    motivo: str = ""
