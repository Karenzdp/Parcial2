from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.db import SessionDep
from app.models import Departamento, DepartamentoCreate, DepartamentoUpdate, Profesor, Curso, DepartamentoCompleto
router = APIRouter()


@router.post("/", response_model=Departamento, status_code=201, summary="Crear departamento")
def crear_departamento(nuevo_departamento: DepartamentoCreate, session: SessionDep):
    """
        Crea un nuevo departamento en el sistema.

        Args:
            nuevo_departamento: Datos del departamento a crear (código, nombre)
            session: Sesión de base de datos

        Returns:
            Departamento: El departamento creado con su ID asignado

        Raises:
            HTTPException 400: Si el código está vacío, no es alfanumérico, tiene longitud incorrecta (2-5 caracteres), el nombre está vacío, o el código ya existe
        """
    errores = []

    nuevo_departamento.codigo = nuevo_departamento.codigo.upper()

    if not nuevo_departamento.codigo.strip():
        errores.append("El código no puede estar vacío")

    elif not nuevo_departamento.codigo.isalnum():
        errores.append("El código solo puede contener letras y números, sin espacios ni símbolos")

    elif len(nuevo_departamento.codigo) < 2 or len(nuevo_departamento.codigo) > 5:
        errores.append("El código debe tener entre 2 y 5 caracteres")
    else:
        result = session.exec(select(Departamento).where(Departamento.codigo == nuevo_departamento.codigo))
        if result.first():
            errores.append("El código del departamento ya existe")

    if not nuevo_departamento.nombre.strip():
        errores.append("El nombre no puede estar vacío")

    if errores:
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": "Errores de validación",
                "errores": errores
            }
        )

    departamento = Departamento.model_validate(nuevo_departamento)
    session.add(departamento)
    session.commit()
    session.refresh(departamento)
    return departamento

@router.get("/{departamento_id}", response_model=DepartamentoCompleto, summary="Obtener departamento completo")
def obtener_departamento(departamento_id: int, session: SessionDep):
    """
        Obtiene un departamento específico con sus profesores y cursos.

        Args:
            departamento_id: ID del departamento a obtener
            session: Sesión de base de datos

        Returns:
            DepartamentoCompleto: Departamento con sus profesores y cursos asociados

        Raises:
            HTTPException 404: Si el departamento no existe
        """
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    return departamento


@router.put("/{departamento_id}", response_model=Departamento, summary="Actualizar departamento")
def actualizar_departamento(departamento_id: int, datos_actualizacion: DepartamentoUpdate, session: SessionDep):
    """
        Actualiza los datos de un departamento existente.

        Args:
            departamento_id: ID del departamento a actualizar
            datos_actualizacion: Campos a actualizar (nombre)
            session: Sesión de base de datos

        Returns:
            Departamento: El departamento actualizado

        Raises:
            HTTPException 400: Si el nombre está vacío
            HTTPException 404: Si el departamento no existe
        """
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    errores = []

    if datos_actualizacion.nombre is not None:
        if not datos_actualizacion.nombre.strip():
            errores.append("El nombre no puede estar vacío")

    if errores:
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": "Errores de validación",
                "errores": errores
            }
        )

    datos = datos_actualizacion.model_dump(exclude_unset=True)
    for key, value in datos.items():
        setattr(departamento, key, value)

    session.add(departamento)
    session.commit()
    session.refresh(departamento)
    return departamento


@router.delete("/{departamento_id}", status_code=204, summary="Eliminar departamento")
def eliminar_departamento(departamento_id: int, session: SessionDep):
    """
        Elimina un departamento del sistema.

        Args:
            departamento_id: ID del departamento a eliminar
            session: Sesión de base de datos

        Returns:
            None: No retorna contenido (status 204)

        Raises:
            HTTPException 400: Si el departamento tiene profesores o cursos asignados
            HTTPException 404: Si el departamento no existe
        """
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    if departamento.profesores:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el departamento porque tiene {len(departamento.profesores)} profesor(es) asignado(s)"
        )

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
    """
        Obtiene la lista de profesores de un departamento.

        Args:
            departamento_id: ID del departamento
            session: Sesión de base de datos

        Returns:
            list[Profesor]: Lista de profesores del departamento

        Raises:
            HTTPException 404: Si el departamento no existe
        """
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    return departamento.profesores


@router.get("/{departamento_id}/cursos", response_model=list[Curso], summary="Cursos de un departamento")
def obtener_cursos_departamento(departamento_id: int, session: SessionDep):
    """
        Obtiene la lista de cursos de un departamento.

        Args:
            departamento_id: ID del departamento
            session: Sesión de base de datos

        Returns:
            list[Curso]: Lista de cursos del departamento

        Raises:
            HTTPException 404: Si el departamento no existe
        """
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    return departamento.cursos


@router.get("/buscar/codigo/{codigo}", response_model=Departamento, summary="Buscar departamento por código")
def buscar_por_codigo(codigo: str, session: SessionDep):
    """
        Busca un departamento por su código.

        Args:
            codigo: Código del departamento a buscar
            session: Sesión de base de datos

        Returns:
            Departamento: El departamento encontrado

        Raises:
            HTTPException 404: Si no se encuentra ningún departamento con ese código
        """
    codigo = codigo.upper()

    result = session.exec(select(Departamento).where(Departamento.codigo == codigo))
    departamento = result.first()

    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    return departamento


@router.get("/buscar/nombre", response_model=list[Departamento], summary="Buscar departamentos por nombre")
def buscar_por_nombre(nombre: str, session: SessionDep):
    """
        Busca departamentos que contengan el nombre especificado.

        Args:
            nombre: Texto a buscar en el nombre del departamento
            session: Sesión de base de datos

        Returns:
            list[Departamento]: Lista de departamentos que coinciden con la búsqueda

        Raises:
            HTTPException 404: Si no se encuentran departamentos con ese nombre
        """
    result = session.exec(
        select(Departamento).where(Departamento.nombre.ilike(f"%{nombre}%"))
    )
    departamentos = result.all()

    if not departamentos:
        raise HTTPException(status_code=404, detail=f"No se encontraron departamentos con '{nombre}' en su nombre")

    return departamentos


@router.get("/listar/todos", response_model=list[Departamento], summary="Listar todos los departamentos")
def listar_todos(session: SessionDep):
    """
        Lista todos los departamentos del sistema.

        Args:
            session: Sesión de base de datos

        Returns:
            list[Departamento]: Lista de todos los departamentos

        Raises:
            HTTPException 404: Si no hay departamentos registrados
        """
    result = session.exec(select(Departamento))
    departamentos = result.all()

    if not departamentos:
        raise HTTPException(status_code=404, detail="No hay departamentos registrados")

    return departamentos