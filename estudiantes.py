from fastapi import APIRouter, HTTPException
from sqlmodel import select
from db import SessionDep
from models import (
    Estudiante, EstudianteCreate, EstudianteUpdate,
    EstudianteConCursos, Curso
)
import re

router=APIRouter()


@router.post("/", response_model=Estudiante, status_code=201, summary="Crear estudiante")
async def crear_estudiante(nuevo_estudiante: EstudianteCreate, session: SessionDep):
    # Validaciones de cédula
    if not nuevo_estudiante.cedula.isdigit():
        raise HTTPException(status_code=400, detail="La cedula solo puede contener números")

    result = await session.exec(select(Estudiante).where(Estudiante.cedula == nuevo_estudiante.cedula))
    if result.first():
        raise HTTPException(status_code=409, detail="La cédula ya existe")

    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, nuevo_estudiante.email):
        raise HTTPException(status_code=400, detail="Formato de email inválido")

    result = await session.exec(select(Estudiante).where(Estudiante.email == nuevo_estudiante.email))
    if result.first():
        raise HTTPException(status_code=409, detail="El email ya existe")


    if not nuevo_estudiante.semestre.isdigit():
        raise HTTPException(status_code=400, detail="El semestre debe ser un número")
    semestre_num = int(nuevo_estudiante.semestre)
    if semestre_num < 1 or semestre_num > 12:
        raise HTTPException(status_code=400, detail="El semestre debe estar entre 1 y 12")

    estudiante = Estudiante.model_validate(nuevo_estudiante)
    session.add(estudiante)
    await session.commit()
    await session.refresh(estudiante)
    return estudiante

@router.get("/{estudiante_id}", response_model=EstudianteconCursos, summary="Obtener estudiante con sus cursos")
async def obtener_estudiantes(estudiante_id:int , session: SessionDep):
    estudiante = await session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return estudiante

@router.put("/{estudiante_id}", response_model=Estudiante, summary="Actualizar estudiante")
async def actualizar_estudiante(estudiante_id:int, datos_actualizacion: EstudianteUpdate, session: SessionDep):
    estudiante= await session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    if datos_actualizacion.nombre is not None:
        if not datos_actualizacion.nombre.strip():
            raise HTTPException( status_code=400, detail="El nombre no puede estar vacio")
        if not all(c.isalpha() or c.isspace() for c in datos_actualizacion.nombre):
            raise HTTPException(status_code=400, detail="El nombre solo puede contener letras y espacios")

    if datos_actualizacion.email is not None:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, datos_actualizacion.email):
            raise HTTPException(status_code=400, detail="Formato de email inválido")

        result = await session.exec(
            select(Estudiante)
            .where(Estudiante.email == datos_actualizacion.email, Estudiante.id != estudiante_id)
        )
        if result.first():
            raise HTTPException(status_code=409, detail="El email ya existe")

        # Validar semestre
    if datos_actualizacion.semestre is not None:
        if not datos_actualizacion.semestre.isdigit():
            raise HTTPException(status_code=400, detail="El semestre debe ser un número")
        semestre_num = int(datos_actualizacion.semestre)
        if semestre_num < 1 or semestre_num > 12:
            raise HTTPException(status_code=400, detail="El semestre debe estar entre 1 y 12")

        # Actualizar campos
    datos = datos_actualizacion.model_dump(exclude_unset=True)
    for key, value in datos.items():
        setattr(estudiante, key, value)

    session.add(estudiante)
    await session.commit()
    await session.refresh(estudiante)
    return estudiante


@router.delete("/{estudiante_id}", status_code=204, summary="Eliminar estudiante")
async def eliminar_estudiante(estudiante_id: int, session: SessionDep):

    estudiante = await session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    await session.delete(estudiante)
    await session.commit()
    return None

@router.get("/{estudiante_id}/cursos", response_model=list[Curso], summary="Cursos de un estudiante")
async def obtener_cursos_estudiante(estudiante_id: int, session: SessionDep):
    """Obtener todos los cursos en los que está matriculado un estudiante"""

    estudiante = await session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return estudiante.cursos