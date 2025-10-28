from fastapi import APIRouter, HTTPException
from db import SessionDep
from db import create_tables
from sqlmodel import select
from models import (
     Curso,CursoCreate, CursoUpdate, CursosConEstudiantes,
    Profesor, Departamento, Estudiante
)

router= APIRouter()

@router.post("/", response_model=Curso, status_code=201, summary="Crear curso")
async def crear_curso(nuevo_curso: CursoCreate , session: SessionDep):

    if not nuevo_curso.codigo.strip():
        raise HTTPException(status_code=400, detail="El codigo no puede estar vacio", )
    result = await session.exec(select(Curso).where(Curso.codigo== nuevo_curso.codigo))
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


@router.get("/{curso_id}/estudiantes", response_model=list[Estudiante], summary="Estudiantes de un curso")
async def obtener_estudiantes_curso(curso_id: int, session: SessionDep):
    curso = await session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    return curso.estudiantes

@router.get("/buscar/codigo/{codigo}", response_model=Curso, summary="Buscar curso por codigo")
async def buscar_por_codigo(codigo: str, session: SessionDep):
    result= await session.exec(select(Curso).where(Curso.codigo == codigo))
    curso= result.first()

    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return curso

@router.get("/buscar/nombre", response_model=list[Curso], summary="Buscar curso por nombre")
async def buscar_por_nombre(nombre:str, session: SessionDep):
    result= await session.exec(select(Curso).where(Curso.nombre.ilike(f"%{nombre}%")))

    cursos= result.all()
    if not cursos:
        raise HTTPException(status_code=404, detaiL=f"No se encontraron cursos con '{nombre}' en su nombre")
    return cursos

@router.get("/buscar/creditos/{creditos}", response_model=list[Curso], summary="Buscar curso por creditos")
async def buscar_por_creditos(creditos:int, session:SessionDep):


    result= await session.exec(select(Curso).where(Curso.creditos == creditos))
    cursos=result.all()

    if not cursos:
        raise HTTPException(status_code=404, detail=f"No se encontraron cursos con {creditos} créditos")

    return cursos


@router.get("/buscar/profesor/{profesor_id}", response_model=list[Curso], summary="Buscar cursos por profesor")
async def buscar_por_profesor(profesor_id: int, session: SessionDep):
    profesor = await session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    result = await session.exec(select(Curso).where(Curso.profesor_id == profesor_id))
    cursos = result.all()

    if not cursos:
        raise HTTPException(status_code=404, detail="El profesor no tiene cursos asignados")

    return cursos


@router.get("/buscar/departamento/{departamento_id}", response_model=list[Curso], summary="Buscar cursos por departamento")
async def buscar_por_departamento(departamento_id: int, session: SessionDep):
    departamento = await session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    result = await session.exec(select(Curso).where(Curso.departamento_id == departamento_id))
    cursos = result.all()

    if not cursos:
        raise HTTPException(status_code=404, detail="El departamento no tiene cursos")

    return cursos