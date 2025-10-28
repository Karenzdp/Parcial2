from fastapi import APIRouter, HTTPException
from sqlmodel import select
from db import SessionDep
from models import (
    Departamento, DepartamentoCreate, DepartamentoUpdate, DepartamentoCompleto,
    Profesor, Curso
)

router = APIRouter()


@router.post("/", response_model=Departamento, status_code=201, summary="Crear departamento")
def crear_departamento(nuevo_departamento: DepartamentoCreate, session: SessionDep):
    """Crear un nuevo departamento"""
    errores = []

    # Convertir código a mayúsculas primero
    nuevo_departamento.codigo = nuevo_departamento.codigo.upper()

    # Validar código
    if not nuevo_departamento.codigo.strip():
        errores.append("El código no puede estar vacío")
    elif not nuevo_departamento.codigo.isalpha():
        errores.append("El código solo puede contener letras")
    elif len(nuevo_departamento.codigo) < 2 or len(nuevo_departamento.codigo) > 5:
        errores.append("El código debe tener entre 2 y 5 letras")
    else:
        # Verificar si el código ya existe (solo si el formato es válido)
        result = session.exec(select(Departamento).where(Departamento.codigo == nuevo_departamento.codigo))
        if result.first():
            errores.append("El código del departamento ya existe")

    # Validar nombre
    if not nuevo_departamento.nombre.strip():
        errores.append("El nombre no puede estar vacío")

    # Si hay errores, lanzar excepción con todos los errores
    if errores:
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": "Errores de validación",
                "errores": errores
            }
        )

    # Crear departamento
    departamento = Departamento.model_validate(nuevo_departamento)
    session.add(departamento)
    session.commit()
    session.refresh(departamento)
    return departamento


@router.get("/{departamento_id}", response_model=DepartamentoCompleto, summary="Obtener departamento completo")
def obtener_departamento(departamento_id: int, session: SessionDep):
    """Obtener un departamento con sus profesores y cursos"""
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    return departamento


@router.put("/{departamento_id}", response_model=Departamento, summary="Actualizar departamento")
def actualizar_departamento(departamento_id: int, datos_actualizacion: DepartamentoUpdate, session: SessionDep):
    """Actualizar información de un departamento"""
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    errores = []

    # Validar nombre
    if datos_actualizacion.nombre is not None:
        if not datos_actualizacion.nombre.strip():
            errores.append("El nombre no puede estar vacío")

    # Si hay errores, lanzar excepción con todos los errores
    if errores:
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": "Errores de validación",
                "errores": errores
            }
        )

    # Actualizar campos
    datos = datos_actualizacion.model_dump(exclude_unset=True)
    for key, value in datos.items():
        setattr(departamento, key, value)

    session.add(departamento)
    session.commit()
    session.refresh(departamento)
    return departamento


@router.delete("/{departamento_id}", status_code=204, summary="Eliminar departamento")
def eliminar_departamento(departamento_id: int, session: SessionDep):
    """Eliminar un departamento"""
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    # Verificar que no tenga profesores
    if departamento.profesores:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el departamento porque tiene {len(departamento.profesores)} profesor(es) asignado(s)"
        )

    # Verificar que no tenga cursos
    if departamento.cursos:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el departamento porque tiene {len(departamento.cursos)} curso(s) asignado(s)"
        )

    session.delete(departamento)
    session.commit()
    return None


@router.get("/{departamento_id}/profesores", response_model=list[Profesor], summary="Profesores de un departamento")
def obtener_profesores_departamento(departamento_id: int, session: SessionDep):
    """Obtener todos los profesores de un departamento"""
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    return departamento.profesores


@router.get("/{departamento_id}/cursos", response_model=list[Curso], summary="Cursos de un departamento")
def obtener_cursos_departamento(departamento_id: int, session: SessionDep):
    """Obtener todos los cursos de un departamento"""
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    return departamento.cursos


@router.get("/buscar/codigo/{codigo}", response_model=Departamento, summary="Buscar departamento por código")
def buscar_por_codigo(codigo: str, session: SessionDep):
    """Buscar un departamento por su código exacto"""
    # Convertir a mayúsculas para buscar
    codigo = codigo.upper()

    result = session.exec(select(Departamento).where(Departamento.codigo == codigo))
    departamento = result.first()

    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    return departamento


@router.get("/buscar/nombre", response_model=list[Departamento], summary="Buscar departamentos por nombre")
def buscar_por_nombre(nombre: str, session: SessionDep):
    """Buscar departamentos por nombre (búsqueda parcial, case-insensitive)"""
    result = session.exec(
        select(Departamento).where(Departamento.nombre.ilike(f"%{nombre}%"))
    )
    departamentos = result.all()

    if not departamentos:
        raise HTTPException(status_code=404, detail=f"No se encontraron departamentos con '{nombre}' en su nombre")

    return departamentos


@router.get("/listar/todos", response_model=list[Departamento], summary="Listar todos los departamentos")
def listar_todos(session: SessionDep):
    """Obtener todos los departamentos"""
    result = session.exec(select(Departamento))
    departamentos = result.all()

    if not departamentos:
        raise HTTPException(status_code=404, detail="No hay departamentos registrados")

    return departamentos