from db import SessionDep
from sqlmodel import select
from fastapi import APIRouter, HTTPException
from models import(
    Profesor, ProfesorUpdate, ProfesorCreate, ProfesorConCursos,
    Curso, Departamento
)

router=APIRouter()

@router.post("/", response_model=Profesor, summary="Crear profesor")
def crear_profesor(nuevo_profesor: ProfesorCreate, session:SessionDep):

    errores=[]

    if not nuevo_profesor.cedula.strip():
        errores.append("El campo cedula no puede estar vacio")
    elif len(nuevo_profesor.cedula)<5 or len(nuevo_profesor.cedula)> 12:
        errores.append("El numero de cédula debe estar entre 5 y 12 dígitos")
    else:
        result=session.exec(select(Profesor).where(Profesor.cedula == nuevo_profesor))
        if result.first():
            errores.append("La cedula ya existe")
    if not nuevo_profesor.nombre.strip():
        errores.append("El nombre no puede estar vacio")
    elif not all(c.isalpha() or c.isspace() for c in nuevo_profesor.nombre):
        errores.append("El nombre solo puede contener letras y espacios")

    if '@' not in nuevo_profesor.email or '.' not in nuevo_profesor.email.split('@')[-1]:
        errores.append("Formato de email inválido")
    else:
        result= session.exec(select(Profesor).where(Profesor.email== nuevo_profesor.email))
        if result.first():
             errores.append("El email ya existe")

    if nuevo_profesor.titulo is not None:
        if not nuevo_profesor.titulo.strip():
            errores.append("El título no puede estar vacío")

    if nuevo_profesor.departamento_id is not None:
        departamento = session.get(Departamento, nuevo_profesor.departamento_id)
        if not departamento:
            errores.append("Departamento no encontrado")

    if errores:
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": "Errores de validación",
                "errores": errores
            }
        )

    profesor = nuevo_profesor.model_dump(exclude_unset=True)
    for key, value in profesor.items():
        setattr(Profesor, key, value)

    session.add(profesor)
    session.commit()
    session.refresh(profesor)
    return profesor


@router.delete("/{profesor_id}", status_code=204, summary="Eliminar profesor")
def eliminar_profesor(profesor_id: int, session: SessionDep):
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    session.delete(profesor)
    session.commit()
    return None


@router.get("/{profesor_id}/cursos", response_model=list[Curso], summary="Cursos de un profesor")
def obtener_cursos_profesor(profesor_id: int, session: SessionDep):
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    return profesor.cursos


@router.get("/buscar/cedula/{cedula}", response_model=Profesor, summary="Buscar profesor por cédula")
def buscar_por_cedula(cedula: str, session: SessionDep):
    result = session.exec(select(Profesor).where(Profesor.cedula == cedula))
    profesor = result.first()

    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    return profesor


@router.get("/buscar/nombre", response_model=list[Profesor], summary="Buscar profesores por nombre")
def buscar_por_nombre(nombre: str, session: SessionDep):
    result = session.exec(
        select(Profesor).where(Profesor.nombre.ilike(f"%{nombre}%"))
    )
    profesores = result.all()

    if not profesores:
        raise HTTPException(status_code=404, detail=f"No se encontraron profesores con '{nombre}' en su nombre")

    return profesores


@router.get("/buscar/titulo", response_model=list[Profesor], summary="Buscar profesores por título")
def buscar_por_titulo(titulo: str, session: SessionDep):
    result = session.exec(
        select(Profesor).where(Profesor.titulo.ilike(f"%{titulo}%"))
    )
    profesores = result.all()

    if not profesores:
        raise HTTPException(status_code=404, detail=f"No se encontraron profesores con título '{titulo}'")

    return profesores


@router.get("/buscar/departamento/{departamento_id}", response_model=list[Profesor],summary="Buscar profesores por departamento")
def buscar_por_departamento(departamento_id: int, session: SessionDep):
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    result = session.exec(select(Profesor).where(Profesor.departamento_id == departamento_id))
    profesores = result.all()

    if not profesores:
        raise HTTPException(status_code=404, detail="El departamento no tiene profesores")

    return profesores


@router.get("/buscar/activos", response_model=list[Profesor], summary="Listar profesores activos")
def buscar_activos(session: SessionDep):
    result = session.exec(select(Profesor).where(Profesor.activo == True))
    profesores = result.all()

    if not profesores:
        raise HTTPException(status_code=404, detail="No hay profesores activos")

    return profesores


@router.get("/buscar/inactivos", response_model=list[Profesor], summary="Listar profesores inactivos")
def buscar_inactivos(session: SessionDep):
    result = session.exec(select(Profesor).where(Profesor.activo == False))
    profesores = result.all()

    if not profesores:
        raise HTTPException(status_code=404, detail="No hay profesores inactivos")

    return profesores
