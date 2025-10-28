from fastapi import APIRouter, HTTPException
from sqlmodel import SessionDep
from db import create_tables
from models import (
    Curso,CursoCreate, CursoUpdate, CursosConEstudiantes,
        Profesor, Departamento, Estudiante
)

router= APIRouter()

@router.post("/", response_model=Curso, status_code=201, summary="Crear curso")
async def crear_curso(nuevo_curso: int , session: SessionDep):

    if not nuevo_curso.codigo.strip():
        raise HTTPException(status_code=400, detail="El codigo no puede estar vacio", )
    result = await session.exec(Select(Curso).where(Curso.codigo== nuevo_curso.codigo))
    if result.first():
        raise HTTPException(status_code=409,detail="El codigo del curso ya existe")

    if not nuevo_curso.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")

    if nuevo_curso.creditos < 1 or nuevo_curso.creditos > 6:
            raise HTTPException(status_code=400, detail="Los créditos deben estar entre 1 y 6")

    if not nuevo_curso.horario.strip():
        raise HTTPException(status_code=400, detail="El horario no puede estar vacío")

    profesor = await session.get(Profesor, nuevo_curso.profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    if not profesor.activo:
        raise HTTPException(status_code=400, detail="El profesor no está activo")

    departamento = await session.get(Departamento, nuevo_curso.departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")


    curso = Curso.model_validate(nuevo_curso)
    session.add(curso)
    await session.commit()
    await session.refresh(curso)
    return curso


@router.get("/{curso_id}", response_model=CursosConEstudiantes, summary="Obtener curso con estudiantes")
async def obtener_curso(curso_id: int, session: SessionDep):
    curso = await session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    return curso


@router.put("/{curso_id}", response_model=Curso, summary="Actualizar curso")
async def actualizar_curso(curso_id: int, datos_actualizacion: CursoUpdate, session: SessionDep):
    """Actualizar información de un curso"""
    curso = await session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    if datos_actualizacion.nombre is not None:
        if not datos_actualizacion.nombre.strip():
            raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")

    if datos_actualizacion.creditos is not None:
        if datos_actualizacion.creditos < 1 or datos_actualizacion.creditos > 6:
            raise HTTPException(status_code=400, detail="Los créditos deben estar entre 1 y 6")

    if datos_actualizacion.horario is not None:
        if not datos_actualizacion.horario.strip():
            raise HTTPException(status_code=400, detail="El horario no puede estar vacío")

    if datos_actualizacion.profesor_id is not None:
        profesor = await session.get(Profesor, datos_actualizacion.profesor_id)
        if not profesor:
            raise HTTPException(status_code=404, detail="Profesor no encontrado")
        if not profesor.activo:
            raise HTTPException(status_code=400, detail="El profesor no está activo")

    datos = datos_actualizacion.model_dump(exclude_unset=True)
    for key, value in datos.items():
        setattr(curso, key, value)

    session.add(curso)
    await session.commit()
    await session.refresh(curso)
    return curso


@router.delete("/{curso_id}", status_code=204, summary="Eliminar curso")
async def eliminar_curso(curso_id: int, session: SessionDep):
    curso = await session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    await session.delete(curso)
    await session.commit()
    return None