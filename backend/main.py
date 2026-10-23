from typing import Optional
from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select

class Candidato(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str
    puesto: str
    telefono: str
    estado: str = "pendiente"

engine = create_engine("sqlite:////data/contrataciones.db")
SQLModel.metadata.create_all(engine)

app = FastAPI(title="Sistema de Contrataciones", root_path="/api")

@app.get("/candidatos")
def listar():
    with Session(engine) as s:
        return s.exec(select(Candidato)).all()

@app.post("/candidatos")
def crear(c: Candidato):
    with Session(engine) as s:
        s.add(c)
        s.commit()
        s.refresh(c)
        return c

@app.patch("/candidatos/{id}")
def cambiar_estado(id: int, estado: str):
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

@app.delete("/candidatos/{id}")
def borrar(id: int):
    with Session(engine) as s:
        c = s.get(Candidato, id)
        if not c:
            raise HTTPException(404, "No encontrado")
        s.delete(c)
        s.commit()
        return {"ok": True}
