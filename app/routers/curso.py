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
    """
        Crea un nuevo curso en el sistema.

        Args:
            nuevo_curso: Datos del curso a crear (código, nombre, créditos, horario, profesor_id, departamento_id)
            session: Sesión de base de datos

        Returns:
            Curso: El curso creado con su ID asignado

        Raises:
            HTTPException 400: Si el código está vacío, nombre vacío, créditos fuera de rango (1-6), horario vacío, o el profesor no está activo
            HTTPException 404: Si el profesor o departamento no existen
            HTTPException 409: Si el código del curso ya existe
        """
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
    """
        Obtiene un curso específico con sus estudiantes, profesor y departamento.

        Args:
            curso_id: ID del curso a obtener
            session: Sesión de base de datos

        Returns:
            CursosConEstudiantes: Curso con sus estudiantes matriculados, profesor y departamento

        Raises:
            HTTPException 404: Si el curso no existe
        """
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    return curso


@router.put("/{curso_id}", response_model=Curso, summary="Actualizar curso")
def actualizar_curso(curso_id: int, datos_actualizacion: CursoUpdate, session: SessionDep):
    """
       Actualiza los datos de un curso existente.

       Args:
           curso_id: ID del curso a actualizar
           datos_actualizacion: Campos a actualizar (nombre, créditos, horario, profesor_id)
           session: Sesión de base de datos

       Returns:
           Curso: El curso actualizado

       Raises:
           HTTPException 400: Si no se envían campos válidos, nombre vacío, créditos fuera de rango (1-6), horario vacío, o el profesor no está activo
           HTTPException 404: Si el curso o el profesor no existen
       """
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


@router.delete("/{curso_id}", status_code=200, summary="Desactivar curso")
def eliminar_curso(curso_id: int, session: SessionDep):
    """
        Desactiva un curso y desmatricula a todos sus estudiantes.

        Args:
            curso_id: ID del curso a desactivar
            session: Sesión de base de datos

        Returns:
            dict: Mensaje de confirmación con información del curso y cantidad de estudiantes desmatriculados

        Raises:
            HTTPException 400: Si el curso ya está inactivo
            HTTPException 404: Si el curso no existe
        """
    from app.models import Matricula

    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    if not curso.activo:
        raise HTTPException(status_code=400, detail="El curso ya está inactivo")

    cantidad_estudiantes = len(curso.estudiantes)
    if cantidad_estudiantes > 0:
        matriculas = session.exec(
            select(Matricula).where(Matricula.curso_id == curso_id)
        ).all()

        for matricula in matriculas:
            session.delete(matricula)

    curso.activo = False
    session.add(curso)
    session.commit()
    session.refresh(curso)

    return {
        "mensaje": "Curso desactivado exitosamente",
        "curso_id": curso_id,
        "codigo": curso.codigo,
        "nombre": curso.nombre,
        "activo": curso.activo,
        "estudiantes_desmatriculados": cantidad_estudiantes  # NUEVO
    }


@router.get("/{curso_id}/estudiantes", response_model=list[Estudiante], summary="Estudiantes de un curso")
def obtener_estudiantes_curso(curso_id: int, session: SessionDep):
    """
        Obtiene la lista de estudiantes matriculados en un curso.

        Args:
            curso_id: ID del curso
            session: Sesión de base de datos

        Returns:
            list[Estudiante]: Lista de estudiantes matriculados en el curso

        Raises:
            HTTPException 404: Si el curso no existe
        """
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    return curso.estudiantes


@router.get("/buscar/codigo/{codigo}", response_model=Curso, summary="Buscar curso por código")
def buscar_por_codigo(codigo: str, session: SessionDep):
    """
        Busca un curso por su código.

        Args:
            codigo: Código del curso a buscar
            session: Sesión de base de datos

        Returns:
            Curso: El curso encontrado

        Raises:
            HTTPException 404: Si no se encuentra ningún curso con ese código
        """
    result = session.exec(select(Curso).where(Curso.codigo.ilike(codigo)))
    curso = result.first()

    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    return curso


@router.get("/buscar/nombre", response_model=list[Curso], summary="Buscar cursos por nombre")
def buscar_por_nombre(nombre: str, session: SessionDep):
    """
        Busca cursos que contengan el nombre especificado.

        Args:
            nombre: Texto a buscar en el nombre del curso
            session: Sesión de base de datos

        Returns:
            list[Curso]: Lista de cursos que coinciden con la búsqueda

        Raises:
            HTTPException 404: Si no se encuentran cursos con ese nombre
        """
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