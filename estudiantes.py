from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from db import SessionDep
from models import (
    Estudiante, EstudianteCreate, EstudianteUpdate,
    EstudianteconCursos, Curso
)
import re

router=APIRouter()

@router.post("/", response_model=Estudiante, status_code=201, summary="Crear estudiante")
async def crear_estudiante(nuevo_estudiante:EstudianteCreate, session: SessionDep):

    if not nuevo_estudiante.cedula.isdigit():
        raise HTTPException(status_code=400, detail="La cedula solo puede contener números")

    if len(nuevo_estudiante.cedula) < 5 or len(nuevo_estudiante.cedula) > 12:
        raise HTTPException(status_code=400, detail="La cédula debe tener entre 5 y 12 dígitos")

    if not nuevo_estudiante.nombre.strip()
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacio")

    if not all(c.isalpha() or c.isspace() for c in nuevo_estudiante.nombre):
        raise HTTPException(status_code=400, detail="El nombre solo puede contener letras y espacios")

