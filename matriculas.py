from fastapi import APIRouter, HTTPException
from sqlmodel import select
from db import SessionDep
from models import Matricula, MatriculaCreate, Estudiante, Curso

router = APIRouter()


@router.post("/", response_model=Matricula, summary="Matricular estudiante en curso")
def crear_matricula(nueva_matricula: MatriculaCreate, session: SessionDep):
    errores = []

    estudiante = session.get(Estudiante, nueva_matricula.estudiante_id)
    if not estudiante:
        errores.append("Estudiante no encontrado")
    elif not estudiante.activo:
        errores.append("El estudiante no está activo")

    curso = session.get(Curso, nueva_matricula.curso_id)
    if not curso:
        errores.append("Curso no encontrado")

    if estudiante and curso:
        result = session.exec(
            select(Matricula).where(
                Matricula.estudiante_id == nueva_matricula.estudiante_id,
                Matricula.curso_id == nueva_matricula.curso_id
            )
        ).first()
        if result:
            errores.append(f"El estudiante ya está matriculado en el curso {curso.nombre}")

    if errores:
        raise HTTPException(status_code=400, detail={"mensaje": "Errores de validación", "errores": errores})

    matricula = Matricula(**nueva_matricula.dict())
    session.add(matricula)
    session.commit()
    session.refresh(matricula)
    return matricula


@router.get("/{estudiante_id}/{curso_id}", response_model=Matricula, summary="Obtener matrícula específica")
def obtener_matricula(estudiante_id: int, curso_id: int, session: SessionDep):
    matricula = session.get(Matricula, (estudiante_id, curso_id))
    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")
    return matricula


@router.delete("/{estudiante_id}/{curso_id}", status_code=200, summary="Eliminar matrícula")
def eliminar_matricula(estudiante_id: int, curso_id: int, session: SessionDep):

    matricula = session.get(Matricula, (estudiante_id, curso_id))
    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")

    # Obtener info antes de eliminar
    estudiante = session.get(Estudiante, estudiante_id)
    curso = session.get(Curso, curso_id)

    session.delete(matricula)
    session.commit()

    return {
        "mensaje": "Matrícula eliminada exitosamente",
        "estudiante": estudiante.nombre if estudiante else "Desconocido",
        "curso": curso.nombre if curso else "Desconocido"
    }


@router.get("/estudiante/{estudiante_id}", response_model=list[Matricula], summary="Matrículas de un estudiante")
def obtener_matriculas_estudiante(estudiante_id: int, session: SessionDep):
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    matriculas = session.exec(select(Matricula).where(Matricula.estudiante_id == estudiante_id)).all()
    return matriculas


@router.get("/curso/{curso_id}", response_model=list[Matricula], summary="Matrículas de un curso")
def obtener_matriculas_curso(curso_id: int, session: SessionDep):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    matriculas = session.exec(select(Matricula).where(Matricula.curso_id == curso_id)).all()
    return matriculas


@router.get("/buscar/curso/{curso_id}", response_model=list[Matricula], summary="Buscar matrículas por curso")
def buscar_matriculas_por_curso(curso_id: int, session: SessionDep):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    matriculas = session.exec(select(Matricula).where(Matricula.curso_id == curso_id)).all()
    if not matriculas:
        raise HTTPException(status_code=404, detail="No hay estudiantes matriculados en este curso")
    return matriculas
