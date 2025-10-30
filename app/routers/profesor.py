from app.db import SessionDep
from sqlmodel import select
from fastapi import APIRouter, HTTPException
from app.models import(
    Profesor, ProfesorUpdate, ProfesorCreate, ProfesorConCursos,
    Curso, Departamento
)

router=APIRouter()

@router.post("/", response_model=Profesor, summary="Crear profesor")
def crear_profesor(nuevo_profesor: ProfesorCreate, session:SessionDep):
    """
        Crea un nuevo profesor en el sistema.

        Args:
            nuevo_profesor: Datos del profesor a crear (cédula, nombre, email, título, departamento_id)
            session: Sesión de base de datos

        Returns:
            Profesor: El profesor creado con su ID asignado

        Raises:
            HTTPException 400: Si la cédula no es numérica, tiene longitud incorrecta (5-12 dígitos), el nombre está vacío o contiene caracteres inválidos, formato de email inválido, título vacío, o algún campo ya existe
            HTTPException 404: Si el departamento no existe
        """
    errores=[]

    if not nuevo_profesor.cedula.isdigit():
        errores.append("La cédula solo puede contener números")
    elif len(nuevo_profesor.cedula)<5 or len(nuevo_profesor.cedula)> 12:
        errores.append("El numero de cédula debe estar entre 5 y 12 dígitos")
    else:
        result=session.exec(select(Profesor).where(Profesor.cedula == nuevo_profesor.cedula))
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

    profesor = Profesor.model_validate(nuevo_profesor)
    session.add(profesor)
    session.commit()
    session.refresh(profesor)
    return profesor


@router.get("/", response_model=list[Profesor], summary="Listar todos los profesores")
def listar_profesores(session: SessionDep):
    """
    Lista todos los profesores del sistema.

    Args:
        session: Sesión de base de datos

    Returns:
        list[Profesor]: Lista de todos los profesores

    Raises:
        HTTPException 404: Si no hay profesores registrados
    """
    result = session.exec(select(Profesor))
    profesores = result.all()

    if not profesores:
        raise HTTPException(status_code=404, detail="No hay profesores registrados")

    return profesores


@router.get("/{profesor_id}", response_model=ProfesorConCursos, summary="Obtener profesor por ID")
def obtener_profesor(profesor_id: int, session: SessionDep):
    """
    Obtiene un profesor específico con sus cursos y departamento.

    Args:
        profesor_id: ID del profesor a obtener
        session: Sesión de base de datos

    Returns:
        ProfesorConCursos: Profesor con sus cursos asignados y departamento

    Raises:
        HTTPException 404: Si el profesor no existe
    """
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    return profesor


@router.put("/{profesor_id}", response_model=Profesor, summary="Actualizar profesor")
def actualizar_profesor(profesor_id: int, datos_actualizacion: ProfesorUpdate, session: SessionDep):
    """
        Actualiza los datos de un profesor existente.

        Args:
            profesor_id: ID del profesor a actualizar
            datos_actualizacion: Campos a actualizar (nombre, email, título, departamento_id, activo)
            session: Sesión de base de datos

        Returns:
            Profesor: El profesor actualizado

        Raises:
            HTTPException 400: Si no se envían campos válidos, nombre contiene caracteres inválidos, o título vacío
            HTTPException 404: Si el profesor o el departamento no existen
        """
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    datos_actualizados = datos_actualizacion.model_dump(exclude_unset=True)
    datos_filtrados = {k: v for k, v in datos_actualizados.items() if not (isinstance(v, str) and not v.strip())}

    if not datos_filtrados:
        raise HTTPException(status_code=400, detail="No se enviaron campos válidos para actualizar")

    if "nombre" in datos_filtrados:
        if not all(c.isalpha() or c.isspace() for c in datos_filtrados["nombre"]):
            raise HTTPException(status_code=400, detail="El nombre solo puede contener letras y espacios")

    if "titulo" in datos_filtrados and not datos_filtrados["titulo"].strip():
        raise HTTPException(status_code=400, detail="El título no puede estar vacío")

    if "departamento_id" in datos_filtrados:
        departamento = session.get(Departamento, datos_filtrados["departamento_id"])
        if not departamento:
            raise HTTPException(status_code=404, detail="Departamento no encontrado")

    for campo, valor in datos_filtrados.items():
        setattr(profesor, campo, valor)

    session.add(profesor)
    session.commit()
    session.refresh(profesor)
    return profesor


@router.delete("/{profesor_id}", status_code=200, summary="Eliminar profesor")
def eliminar_profesor(profesor_id: int, session: SessionDep):
    """
        Desactiva un profesor del sistema.

        Args:
            profesor_id: ID del profesor a desactivar
            session: Sesión de base de datos

        Returns:
            dict: Mensaje de confirmación con información del profesor desactivado

        Raises:
            HTTPException 400: Si el profesor ya está inactivo o tiene cursos asignados
            HTTPException 404: Si el profesor no existe
        """
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    if not profesor.activo:
        raise HTTPException(status_code=400, detail="El profesor ya está eliminadoo")

    if profesor.cursos:
        cursos_activos = [c.nombre for c in profesor.cursos]
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": "No se puede eliminar el profesor porque tiene cursos asignados",
                "cursos": cursos_activos,
                "sugerencia": "Reasigne los cursos a otro profesor antes de desactivar"
            }
        )

    profesor.activo = False
    session.add(profesor)
    session.commit()
    session.refresh(profesor)

    return {
        "mensaje": "Profesor desactivado exitosamente",
        "profesor_id": profesor_id,
        "nombre": profesor.nombre,
        "activo": profesor.activo
    }


@router.get("/{profesor_id}/cursos", response_model=list[Curso], summary="Cursos de un profesor")
def obtener_cursos_profesor(profesor_id: int, session: SessionDep):
    """
        Obtiene la lista de cursos asignados a un profesor.

        Args:
            profesor_id: ID del profesor
            session: Sesión de base de datos

        Returns:
            list[Curso]: Lista de cursos del profesor

        Raises:
            HTTPException 404: Si el profesor no existe
        """
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    return profesor.cursos


@router.get("/buscar/cedula/{cedula}", response_model=Profesor, summary="Buscar profesor por cédula")
def buscar_por_cedula(cedula: str, session: SessionDep):
    """
        Busca un profesor por su cédula.

        Args:
            cedula: Cédula del profesor a buscar
            session: Sesión de base de datos

        Returns:
            Profesor: El profesor encontrado

        Raises:
            HTTPException 404: Si no se encuentra ningún profesor con esa cédula
        """
    result = session.exec(select(Profesor).where(Profesor.cedula == cedula))
    profesor = result.first()

    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    return profesor


@router.get("/buscar/nombre", response_model=list[Profesor], summary="Buscar profesores por nombre")
def buscar_por_nombre(nombre: str, session: SessionDep):
    """
        Busca profesores que contengan el nombre especificado.

        Args:
            nombre: Texto a buscar en el nombre del profesor
            session: Sesión de base de datos

        Returns:
            list[Profesor]: Lista de profesores que coinciden con la búsqueda

        Raises:
            HTTPException 404: Si no se encuentran profesores con ese nombre
        """
    result = session.exec(
        select(Profesor).where(Profesor.nombre.ilike(f"%{nombre}%"))
    )
    profesores = result.all()

    if not profesores:
        raise HTTPException(status_code=404, detail=f"No se encontraron profesores con '{nombre}' en su nombre")

    return profesores


@router.get("/buscar/titulo", response_model=list[Profesor], summary="Buscar profesores por título")
def buscar_por_titulo(titulo: str, session: SessionDep):
    """
        Busca profesores que contengan el título especificado.

        Args:
            titulo: Texto a buscar en el título del profesor (ej: PhD, MSc, Ingeniero)
            session: Sesión de base de datos

        Returns:
            list[Profesor]: Lista de profesores que coinciden con la búsqueda

        Raises:
            HTTPException 404: Si no se encuentran profesores con ese título
        """
    result = session.exec(
        select(Profesor).where(Profesor.titulo.ilike(f"%{titulo}%"))
    )
    profesores = result.all()

    if not profesores:
        raise HTTPException(status_code=404, detail=f"No se encontraron profesores con título '{titulo}'")

    return profesores


@router.get("/buscar/departamento/{departamento_id}", response_model=list[Profesor],summary="Buscar profesores por departamento")
def buscar_por_departamento(departamento_id: int, session: SessionDep):
    """
        Busca todos los profesores de un departamento.

        Args:
            departamento_id: ID del departamento
            session: Sesión de base de datos

        Returns:
            list[Profesor]: Lista de profesores del departamento

        Raises:
            HTTPException 404: Si el departamento no existe o no tiene profesores
        """
    departamento = session.get(Departamento, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento no encontrado")

    result = session.exec(select(Profesor).where(Profesor.departamento_id == departamento_id))
    profesores = result.all()

    if not profesores:
        raise HTTPException(status_code=404, detail="El departamento no tiene profesores")

    return profesores


