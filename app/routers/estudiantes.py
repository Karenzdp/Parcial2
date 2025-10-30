from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.db import SessionDep
from app.models import (
    Estudiante, EstudianteCreate, EstudianteUpdate,
    EstudianteConCursos, Curso
)

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


@router.get("/", response_model=list[Estudiante], summary="Listar todos los estudiantes")
def listar_estudiantes(session: SessionDep):
    result = session.exec(select(Estudiante))
    estudiantes = result.all()

    if not estudiantes:
        raise HTTPException(status_code=404, detail="No hay estudiantes registrados")

    return estudiantes
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

    datos_actualizados = datos_actualizacion.model_dump(exclude_unset=True)

    datos_filtrados = {k: v for k, v in datos_actualizados.items() if not (isinstance(v, str) and not v.strip())}

    if not datos_filtrados:
        raise HTTPException(status_code=400, detail="No se enviaron campos válidos para actualizar")

    if "nombre" in datos_filtrados:
        if not all(c.isalpha() or c.isspace() for c in datos_filtrados["nombre"]):
            raise HTTPException(status_code=400, detail="El nombre solo puede contener letras y espacios")

    if "email" in datos_filtrados:
        email = datos_filtrados["email"].strip()
        if email:
            if "@" not in email or "." not in email.split("@")[-1]:
                raise HTTPException(status_code=400, detail="Formato de email inválido")

            existe_email = session.exec(
                select(Estudiante).where(Estudiante.email == email, Estudiante.id != estudiante_id)
            ).first()
            if existe_email:
                raise HTTPException(status_code=409, detail="El email ya está registrado")

        else:
            datos_filtrados["email"] = None

    if "semestre" in datos_filtrados:
        semestre = datos_filtrados["semestre"]
        if not semestre.isdigit():
            raise HTTPException(status_code=400, detail="El semestre debe ser un número")
        if not (1 <= int(semestre) <= 12):
            raise HTTPException(status_code=400, detail="El semestre debe estar entre 1 y 12")

    for campo, valor in datos_filtrados.items():
        setattr(estudiante, campo, valor)

    session.add(estudiante)
    session.commit()
    session.refresh(estudiante)

    return estudiante


@router.delete("/{estudiante_id}", status_code=200, summary="Desactivar estudiante")
def eliminar_estudiante(estudiante_id: int, session: SessionDep):
    from app.models import Matricula

    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    if not estudiante.activo:
        raise HTTPException(status_code=400, detail="El estudiante ya está inactivo")

    cantidad_cursos = len(estudiante.cursos)
    if cantidad_cursos > 0:
        matriculas = session.exec(
            select(Matricula).where(Matricula.estudiante_id == estudiante_id)
        ).all()

        for matricula in matriculas:
            session.delete(matricula)

    estudiante.activo = False
    session.add(estudiante)
    session.commit()
    session.refresh(estudiante)

    return {
        "mensaje": "Estudiante desactivado exitosamente",
        "estudiante_id": estudiante_id,
        "nombre": estudiante.nombre,
        "activo": estudiante.activo,
        "cursos_desmatriculados": cantidad_cursos
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