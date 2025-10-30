from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.db import SessionDep
from app.models import Matricula, MatriculaCreate, Estudiante, Curso

router = APIRouter()


## ✅ 1. CREAR MATRÍCULA
@router.post("/", response_model=Matricula, status_code=201, summary="Matricular estudiante en curso")
def matricular_estudiante(nueva_matricula: MatriculaCreate, session: SessionDep):
    estudiante = session.get(Estudiante, nueva_matricula.estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    curso = session.get(Curso, nueva_matricula.curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    # Verificar si YA existe la matrícula
    result = session.exec(
        select(Matricula).where(
            Matricula.estudiante_id == nueva_matricula.estudiante_id,
            Matricula.curso_id == nueva_matricula.curso_id
        )
    )
    if result.first():
        raise HTTPException(status_code=409, detail="El estudiante ya está matriculado en este curso")

    matricula = Matricula.model_validate(nueva_matricula)
    session.add(matricula)
    session.commit()
    session.refresh(matricula)
    return matricula


## 🗑️ 2. DESMATRICULAR ESTUDIANTE
@router.delete("/{estudiante_id}/{curso_id}", status_code=204, summary="Desmatricular estudiante")
def desmatricular_estudiante(
        estudiante_id: int,
        curso_id: int,
        session: SessionDep
):
    """Eliminar la matrícula de un estudiante en un curso"""

    matricula = session.get(Matricula, (estudiante_id, curso_id))

    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")

    session.delete(matricula)
    session.commit()
    return None


## 📚 3. OBTENER MATRÍCULAS POR ESTUDIANTE
@router.get("/estudiante/{estudiante_id}", response_model=list[Matricula], summary="Matrículas de un estudiante")
def obtener_matriculas_estudiante(estudiante_id: int, session: SessionDep):
    """Obtener todas las matrículas de un estudiante"""

    # Verificar que el estudiante existe
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Obtener las matrículas usando select directo
    matriculas = session.exec(
        select(Matricula).where(Matricula.estudiante_id == estudiante_id)
    ).all()

    return matriculas


## 🧑‍🏫 4. OBTENER MATRÍCULAS POR CURSO
@router.get("/curso/{curso_id}", response_model=list[Matricula], summary="Matrículas de un curso")
def obtener_matriculas_curso(curso_id: int, session: SessionDep):
    """Obtener todas las matrículas de un curso"""

    # Verificar que el curso existe
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    # Obtener las matrículas usando select directo
    matriculas = session.exec(
        select(Matricula).where(Matricula.curso_id == curso_id)
    ).all()

    return matriculas