from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.db import SessionDep
from app.models import (
    Curso, CursoCreate, CursoUpdate, CursosConEstudiantes,
    Profesor, Departamento, Estudiante
)

router = APIRouter()


@router.post("/", response_model=Curso, status_code=201, summary="Crear curso")
def crear_curso(nuevo_curso: CursoCreate, session: SessionDep):

    if not nuevo_curso.codigo.strip():
        raise HTTPException(status_code=400, detail="El código no puede estar vacío")

    result = session.exec(select(Curso).where(Curso.codigo == nuevo_curso.codigo))
    if result.first():
        raise HTTPException(status_code=409, detail="El código del curso ya existe")

    if not nuevo_curso.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")

    if nuevo_curso.creditos < 1 or nuevo_curso.creditos > 6:
        raise HTTPException(status_code=400, detail="Los créditos deben estar entre 1 y 6")

    if not nuevo_curso.horario.strip():
        raise HTTPException(status_code=400, detail="El horario no puede estar vacío")

    profesor = session.get(Profesor, nuevo_curso.profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    if not profesor.activo:
        raise HTTPException(status_code=400, detail="El profesor no está activo")

    departamento = session.get(Departamento, nuevo_curso.departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    curso = Curso.model_validate(nuevo_curso)
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return curso


@router.get("/{curso_id}", response_model=CursosConEstudiantes, summary="Obtener curso con estudiantes")
def obtener_curso(curso_id: int, session: SessionDep):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    return curso


@router.put("/{curso_id}", response_model=Curso, summary="Actualizar curso")
def actualizar_curso(curso_id: int, datos_actualizacion: CursoUpdate, session: SessionDep):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    datos_actualizados = datos_actualizacion.model_dump(exclude_unset=True)
    datos_filtrados = {k: v for k, v in datos_actualizados.items() if not (isinstance(v, str) and not v.strip())}

    if not datos_filtrados:
        raise HTTPException(status_code=400, detail="No se enviaron campos válidos para actualizar")

    # Validaciones
    if "nombre" in datos_filtrados and not datos_filtrados["nombre"].strip():
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")

    if "creditos" in datos_filtrados:
        creditos = datos_filtrados["creditos"]
        if not (1 <= creditos <= 6):
            raise HTTPException(status_code=400, detail="Los créditos deben estar entre 1 y 6")

    if "horario" in datos_filtrados and not datos_filtrados["horario"].strip():
        raise HTTPException(status_code=400, detail="El horario no puede estar vacío")

    if "profesor_id" in datos_filtrados:
        profesor = session.get(Profesor, datos_filtrados["profesor_id"])
        if not profesor:
            raise HTTPException(status_code=404, detail="Profesor no encontrado")
        if not profesor.activo:
            raise HTTPException(status_code=400, detail="El profesor no está activo")

    for campo, valor in datos_filtrados.items():
        setattr(curso, campo, valor)

    session.add(curso)
    session.commit()
    session.refresh(curso)
    return curso



@router.delete("/{curso_id}", status_code=200, summary="Desactivar curso (soft delete)")
def eliminar_curso(curso_id: int, session: SessionDep):

    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    if not curso.activo:
        raise HTTPException(status_code=400, detail="El curso ya está inactivo")

    if curso.estudiantes:
        cantidad_estudiantes = len(curso.estudiantes)
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": f"No se puede desactivar el curso porque tiene {cantidad_estudiantes} estudiante(s) matriculado(s)",
                "sugerencia": "Desmatricule a los estudiantes antes de desactivar el curso"
            }
        )

    curso.activo = False
    session.add(curso)
    session.commit()
    session.refresh(curso)

    return {
        "mensaje": "Curso desactivado exitosamente",
        "curso_id": curso_id,
        "codigo": curso.codigo,
        "nombre": curso.nombre,
        "activo": curso.activo
    }


@router.get("/{curso_id}/estudiantes", response_model=list[Estudiante], summary="Estudiantes de un curso")
def obtener_estudiantes_curso(curso_id: int, session: SessionDep):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    return curso.estudiantes


@router.get("/buscar/codigo/{codigo}", response_model=Curso, summary="Buscar curso por código")
def buscar_por_codigo(codigo: str, session: SessionDep):
    result = session.exec(select(Curso).where(Curso.codigo == codigo))
    curso = result.first()

    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    return curso


@router.get("/buscar/nombre", response_model=list[Curso], summary="Buscar cursos por nombre")
def buscar_por_nombre(nombre: str, session: SessionDep):
    result = session.exec(
        select(Curso).where(Curso.nombre.ilike(f"%{nombre}%"))
    )
    cursos = result.all()

    if not cursos:
        raise HTTPException(status_code=404, detail=f"No se encontraron cursos con '{nombre}' en su nombre")

    return cursos


@router.get("/buscar/creditos/{creditos}", response_model=list[Curso], summary="Buscar cursos por créditos")
def buscar_por_creditos(creditos: int, session: SessionDep):
    if creditos < 1 or creditos > 6:
        raise HTTPException(status_code=400, detail="Los créditos deben estar entre 1 y 6")

    result = session.exec(select(Curso).where(Curso.creditos == creditos))
    cursos = result.all()

    if not cursos:
        raise HTTPException(status_code=404, detail=f"No se encontraron cursos con {creditos} créditos")

    return cursos


@router.get("/buscar/profesor/{profesor_id}", response_model=list[Curso], summary="Buscar cursos por profesor")
def buscar_por_profesor(profesor_id: int, session: SessionDep):
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    result = session.exec(select(Curso).where(Curso.profesor_id == profesor_id))
    cursos = result.all()

    if not cursos:
        raise HTTPException(status_code=404, detail="El profesor no tiene cursos asignados")

    return cursos


@router.get("/buscar/departamento/{departamento_id}", response_model=list[Curso],
            summary="Buscar cursos por departamento")
def buscar_por_departamento(departamento_id: int, session: SessionDep):
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    result = session.exec(select(Curso).where(Curso.departamento_id == departamento_id))
    cursos = result.all()

    if not cursos:
        raise HTTPException(status_code=404, detail="El departamento no tiene cursos")

    return cursos