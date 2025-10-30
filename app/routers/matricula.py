from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.db import SessionDep
from app.models import Matricula, MatriculaCreate, Estudiante, Curso

router = APIRouter()


@router.post("/", response_model=Matricula, status_code=201, summary="Matricular estudiante en curso")
def matricular_estudiante(nueva_matricula: MatriculaCreate, session: SessionDep):
    """
        Matricula un estudiante en un curso.

        Args:
            nueva_matricula: Datos de la matrícula (estudiante_id, curso_id)
            session: Sesión de base de datos

        Returns:
            Matricula: La matrícula creada

        Raises:
            HTTPException 404: Si el estudiante o curso no existen
            HTTPException 409: Si el estudiante ya está matriculado en ese curso
        """
    estudiante = session.get(Estudiante, nueva_matricula.estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    curso = session.get(Curso, nueva_matricula.curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

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


@router.delete("/{estudiante_id}/{curso_id}", status_code=204, summary="Desmatricular estudiante")
def desmatricular_estudiante(estudiante_id: int, curso_id: int,session: SessionDep):
    """
        Desmatricula un estudiante de un curso.

        Args:
            estudiante_id: ID del estudiante
            curso_id: ID del curso
            session: Sesión de base de datos

        Returns:
            None: No retorna contenido (status 204)

        Raises:
            HTTPException 404: Si la matrícula no existe
        """
    matricula = session.get(Matricula, (estudiante_id, curso_id))

    if not matricula:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")

    session.delete(matricula)
    session.commit()
    return None


@router.get("/estudiante/{estudiante_id}", response_model=list[Matricula], summary="Matrículas de un estudiante")
def obtener_matriculas_estudiante(estudiante_id: int, session: SessionDep):
    """
       Obtiene todas las matrículas de un estudiante.

       Args:
           estudiante_id: ID del estudiante
           session: Sesión de base de datos

       Returns:
           list[Matricula]: Lista de matrículas del estudiante

       Raises:
           HTTPException 404: Si el estudiante no existe
       """

    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    matriculas = session.exec(
        select(Matricula).where(Matricula.estudiante_id == estudiante_id)
    ).all()

    return matriculas


@router.get("/curso/{curso_id}", response_model=list[Matricula], summary="Matrículas de un curso")
def obtener_matriculas_curso(curso_id: int, session: SessionDep):
    """
        Obtiene todas las matrículas de un curso.

        Args:
            curso_id: ID del curso
            session: Sesión de base de datos

        Returns:
            list[Matricula]: Lista de matrículas del curso

        Raises:
            HTTPException 404: Si el curso no existe
        """
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    matriculas = session.exec(
        select(Matricula).where(Matricula.curso_id == curso_id)
    ).all()

    return matriculas