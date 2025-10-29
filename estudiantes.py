from fastapi import APIRouter, HTTPException
from sqlmodel import select
from db import SessionDep
from models import (
    Estudiante, EstudianteCreate, EstudianteUpdate,
    EstudianteConCursos, Curso
)
import re

router = APIRouter()


@router.post("/", response_model=Estudiante, status_code=201, summary="Crear estudiante")
def crear_estudiante(nuevo_estudiante: EstudianteCreate, session: SessionDep):
    errores = []

    if not nuevo_estudiante.cedula.isdigit():
        errores.append("La cédula solo puede contener números")
    elif len(nuevo_estudiante.cedula) < 5 or len(nuevo_estudiante.cedula) > 12:
        errores.append("La cédula debe tener entre 5 y 12 dígitos")
    else:
        result = session.exec(select(Estudiante).where(Estudiante.cedula == nuevo_estudiante.cedula))
        if result.first():
            errores.append("La cédula ya existe")

    if not nuevo_estudiante.nombre.strip():
        errores.append("El nombre no puede estar vacío")
    elif not all(c.isalpha() or c.isspace() for c in nuevo_estudiante.nombre):
        errores.append("El nombre solo puede contener letras y espacios")

    if '@' not in nuevo_estudiante.email or '.' not in nuevo_estudiante.email.split('@')[-1]:
        errores.append("Formato de email inválido")
    else:
        result = session.exec(select(Estudiante).where(Estudiante.email == nuevo_estudiante.email))
        if result.first():
            errores.append("El email ya existe")

    if not nuevo_estudiante.semestre.isdigit():
        errores.append("El semestre debe ser un número")
    else:
        semestre_num = int(nuevo_estudiante.semestre)
        if semestre_num < 1 or semestre_num > 12:
            errores.append("El semestre debe estar entre 1 y 12")

    if errores:
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": "Errores de validación",
                "errores": errores
            }
        )

    estudiante = Estudiante.model_validate(nuevo_estudiante)
    session.add(estudiante)
    session.commit()
    session.refresh(estudiante)
    return estudiante


@router.get("/{estudiante_id}", response_model=EstudianteConCursos, summary="Obtener estudiante con sus cursos")
def obtener_estudiante(estudiante_id: int, session: SessionDep):
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return estudiante


@router.put("/{estudiante_id}", response_model=Estudiante, summary="Actualizar estudiante")
def actualizar_estudiante(estudiante_id: int, datos_actualizacion: EstudianteUpdate, session: SessionDep):
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    if datos_actualizacion.nombre is not None:
        if not datos_actualizacion.nombre.strip():
            raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")
        if not all(c.isalpha() or c.isspace() for c in datos_actualizacion.nombre):
            raise HTTPException(status_code=400, detail="El nombre solo puede contener letras y espacios")

    if datos_actualizacion.email is not None:
        if '@' not in datos_actualizacion.email or '.' not in datos_actualizacion.email.split('@')[-1]:
            raise HTTPException(status_code=400, detail="Formato de email inválido")

        result = session.exec(
            select(Estudiante)
            .where(Estudiante.email == datos_actualizacion.email, Estudiante.id != estudiante_id)
        )
        if result.first():
            raise HTTPException(status_code=409, detail="El email ya existe")


    if datos_actualizacion.semestre is not None:
        if not datos_actualizacion.semestre.isdigit():
            raise HTTPException(status_code=400, detail="El semestre debe ser un número")
        semestre_num = int(datos_actualizacion.semestre)
        if semestre_num < 1 or semestre_num > 12:
            raise HTTPException(status_code=400, detail="El semestre debe estar entre 1 y 12")

    datos = datos_actualizacion.model_dump(exclude_unset=True)
    for key, value in datos.items():
        setattr(estudiante, key, value)

    session.add(estudiante)
    session.commit()
    session.refresh(estudiante)
    return estudiante


@router.delete("/{estudiante_id}", status_code=200, summary="Desactivar estudiante (soft delete)")
def eliminar_estudiante(estudiante_id: int, session: SessionDep):
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    if not estudiante.activo:
        raise HTTPException(status_code=400, detail="El estudiante ya está inactivo")

    estudiante.activo = False
    session.add(estudiante)
    session.commit()
    session.refresh(estudiante)

    return {
        "mensaje": "Estudiante desactivado exitosamente",
        "estudiante_id": estudiante_id,
        "nombre": estudiante.nombre,
        "activo": estudiante.activo
    }


@router.get("/{estudiante_id}/cursos", response_model=list[Curso], summary="Cursos de un estudiante")
def obtener_cursos_estudiante(estudiante_id: int, session: SessionDep):
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return estudiante.cursos


@router.get("/buscar/cedula/{cedula}", response_model=Estudiante, summary="Buscar estudiante por cédula")
def buscar_por_cedula(cedula: str, session: SessionDep):
    result = session.exec(select(Estudiante).where(Estudiante.cedula == cedula))
    estudiante = result.first()

    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return estudiante


@router.get("/buscar/semestre/{semestre}", response_model=list[Estudiante], summary="Buscar estudiantes por semestre")
def buscar_por_semestre(semestre: str, session: SessionDep):
    result = session.exec(select(Estudiante).where(Estudiante.semestre == semestre))
    estudiantes = result.all()

    if not estudiantes:
        raise HTTPException(status_code=404, detail="No se encontraron estudiantes en ese semestre")

    return estudiantes


@router.get("/buscar/nombre", response_model=list[Estudiante], summary="Buscar estudiantes por nombre")
def buscar_por_nombre(nombre: str, session: SessionDep):

    result = session.exec(
        select(Estudiante).where(Estudiante.nombre.ilike(f"%{nombre}%"))
    )
    estudiantes = result.all()

    if not estudiantes:
        raise HTTPException(status_code=404, detail=f"No se encontraron estudiantes con '{nombre}' en su nombre")

    return estudiantes