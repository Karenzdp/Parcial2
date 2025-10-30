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
    """
       Crea un nuevo estudiante en el sistema.

       Args:
           nuevo_estudiante: Datos del estudiante a crear (cédula, nombre, email, semestre)
           session: Sesión de base de datos

       Returns:
           Estudiante: El estudiante creado con su ID asignado

       Raises:
           HTTPException 400: Si la cédula no es numérica, tiene longitud incorrecta (5-12 dígitos), el nombre está vacío o contiene caracteres inválidos, formato de email inválido, semestre no es numérico o está fuera de rango (1-12), o algún campo ya existe
       """
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
    """
        Lista todos los estudiantes del sistema.

        Args:
            session: Sesión de base de datos

        Returns:
            list[Estudiante]: Lista de todos los estudiantes

        Raises:
            HTTPException 404: Si no hay estudiantes registrados
        """
    result = session.exec(select(Estudiante))
    estudiantes = result.all()

    if not estudiantes:
        raise HTTPException(status_code=404, detail="No hay estudiantes registrados")

    return estudiantes
@router.get("/{estudiante_id}", response_model=EstudianteConCursos, summary="Obtener estudiante con sus cursos")
def obtener_estudiante(estudiante_id: int, session: SessionDep):
    """
        Obtiene un estudiante específico con sus cursos matriculados.

        Args:
            estudiante_id: ID del estudiante a obtener
            session: Sesión de base de datos

        Returns:
            EstudianteConCursos: Estudiante con sus cursos matriculados

        Raises:
            HTTPException 404: Si el estudiante no existe
        """
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return estudiante


@router.put("/{estudiante_id}", response_model=Estudiante, summary="Actualizar estudiante")
def actualizar_estudiante(estudiante_id: int, datos_actualizacion: EstudianteUpdate, session: SessionDep):
    """
        Actualiza los datos de un estudiante existente.

        Args:
            estudiante_id: ID del estudiante a actualizar
            datos_actualizacion: Campos a actualizar (nombre, email, semestre, activo)
            session: Sesión de base de datos

        Returns:
            Estudiante: El estudiante actualizado

        Raises:
            HTTPException 400: Si no se envían campos válidos, nombre contiene caracteres inválidos, formato de email inválido, semestre no numérico o fuera de rango (1-12)
            HTTPException 404: Si el estudiante no existe
            HTTPException 409: Si el email ya está registrado por otro estudiante
        """
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
    """
        Desactiva un estudiante y lo desmatricula de todos sus cursos.

        Args:
            estudiante_id: ID del estudiante a desactivar
            session: Sesión de base de datos

        Returns:
            dict: Mensaje de confirmación con información del estudiante y cantidad de cursos desmatriculados

        Raises:
            HTTPException 400: Si el estudiante ya está inactivo
            HTTPException 404: Si el estudiante no existe
        """
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
    """
       Obtiene la lista de cursos en los que está matriculado un estudiante.

       Args:
           estudiante_id: ID del estudiante
           session: Sesión de base de datos

       Returns:
           list[Curso]: Lista de cursos del estudiante

       Raises:
           HTTPException 404: Si el estudiante no existe
       """
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return estudiante.cursos


@router.get("/buscar/cedula/{cedula}", response_model=Estudiante, summary="Buscar estudiante por cédula")
def buscar_por_cedula(cedula: str, session: SessionDep):
    """
        Busca un estudiante por su cédula.

        Args:
            cedula: Cédula del estudiante a buscar
            session: Sesión de base de datos

        Returns:
            Estudiante: El estudiante encontrado

        Raises:
            HTTPException 404: Si no se encuentra ningún estudiante con esa cédula
        """
    result = session.exec(select(Estudiante).where(Estudiante.cedula == cedula))
    estudiante = result.first()

    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return estudiante


@router.get("/buscar/semestre/{semestre}", response_model=list[Estudiante], summary="Buscar estudiantes por semestre")
def buscar_por_semestre(semestre: str, session: SessionDep):
    """
        Busca estudiantes de un semestre específico.

        Args:
            semestre: Semestre a buscar (1-12)
            session: Sesión de base de datos

        Returns:
            list[Estudiante]: Lista de estudiantes del semestre especificado

        Raises:
            HTTPException 404: Si no se encuentran estudiantes en ese semestre
        """
    result = session.exec(select(Estudiante).where(Estudiante.semestre == semestre))
    estudiantes = result.all()

    if not estudiantes:
        raise HTTPException(status_code=404, detail="No se encontraron estudiantes en ese semestre")

    return estudiantes


@router.get("/buscar/nombre", response_model=list[Estudiante], summary="Buscar estudiantes por nombre")
def buscar_por_nombre(nombre: str, session: SessionDep):
    """
        Busca estudiantes que contengan el nombre especificado.

        Args:
            nombre: Texto a buscar en el nombre del estudiante
            session: Sesión de base de datos

        Returns:
            list[Estudiante]: Lista de estudiantes que coinciden con la búsqueda

        Raises:
            HTTPException 404: Si no se encuentran estudiantes con ese nombre
        """

    result = session.exec(
        select(Estudiante).where(Estudiante.nombre.ilike(f"%{nombre}%"))
    )
    estudiantes = result.all()

    if not estudiantes:
        raise HTTPException(status_code=404, detail=f"No se encontraron estudiantes con '{nombre}' en su nombre")

    return estudiantes