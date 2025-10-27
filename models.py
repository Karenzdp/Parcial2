from operator import index

from sqlalchemy.orm import relationship
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from pydantic import field_validator, EmailStr

# MODELOS BASE

class EstudianteBase(SQLModel):
    cedula: str = Field(unique=True, index=True, description="Cédula única estudiante")
    nombre: str = Field(description="Nombre completo estudiante")
    email: str = Field(unique=True, description="Email institucional estudiante")
    semestre: str = Field(description="Semestre actual estudiante")
    activo: bool = Field(default=True, description="Estado estudiante")

class CursoBase(SQLModel):
    codigo: str = Field(unique=True, index=True , description="Codigo curso")
    nombre: str = Field(description="Nombre curso")
    creditos: int= Field(description="Creditos curso")
    horario: str = Field(description= "Horario curso (ej: Lunes 8-10)")

class ProfesorBase(SQLModel):
    cedula: str = Field(unique=True, index=True, description="Cedula unica profesor")
    nombre: str = Field(description="Nombre profesor")
    email: str = Field(description="Email profesor")
    titulo : str = Field(description="Titulo profesor (ej: PhD, MSc, Ingeniero)")
    activo: bool = Field(default=True, description="Estado del profesor")

class DepartamentoBase(SQLModel):
    codigo: str = Field(unique=True, index= True ,description="Codigo departamento (ej: ING, HUM)")
    nombre: str = Field(description="Nombre departamento")


class Matricula(SQLModel, table=True):
    estudiante_id: int = Field(foreign_key="estudiante.id", primary_key=True)
    curso_id: int = Field(foreign_key="curso.id", primary_key=True)
    nota_final: Optional[float] = Field(default=None, ge=0.0, le=5.0, description="Nota final del curso (0.0 - 5.0)")
    aprobado: Optional[bool] = Field(default=None, description="Si aprobó o no el curso (>=3.0)")



#MODELOS TABLA
class Estudiante(EstudianteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cursos: list["Curso"] = Relationship(back_populates="estudiantes", link_model=Matricula)

class Departamento(CursoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    profesores: list["Profesor"] = Relationship(back_populates="cursos")
    cursos: list["Curso"] = Relationship(back_populates="profesores")

class Profesor(ProfesorBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    departamento_id: Optional[int] = Field(default=None, foreign_key="departamento.id")
    departamento= Departamento= relationship(back_populates="profesores")
    cursos: list["Curso"] = Relationship(back_populates="profesor")

class Curso(CursoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    profesor_id: int = Field(foreign_key="profesor.id")
    departamento_id: int = Field(foreign_key="departamento.id")

    profesor: Profesor = Relationship(back_populates="cursos")

    # Relación N:1 con Departamento
    departamento: Departamento = Relationship(back_populates="cursos")

    # Relación N:M con Estudiante a través de Matricula
    estudiantes: list[Estudiante] = Relationship(back_populates="cursos", link_model=Matricula)



#MODELOS PARA OPERACIONES

class EstudianteCreate(EstudianteBase):
    pass


class EstudianteUpdate(SQLModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    semestre: Optional[int] = Field(default=None, ge=1, le=12)
    activo: Optional[bool] = None


class CursoCreate(CursoBase):
    profesor_id: int
    departamento_id: int


class CursoUpdate(SQLModel):
    nombre: Optional[str] = None
    creditos: Optional[int] = None
    horario: Optional[str] = None
    profesor_id: Optional[int] = None

class ProfesorCreate(ProfesorBase):
    departamento_id: int


class ProfesorUpdate(SQLModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    titulo: Optional[str] = None
    departamento_id: Optional[int] = None
    activo: Optional[bool] = None


class DepartamentoCreate(DepartamentoBase):
    pass


class DepartamentoUpdate(SQLModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None


class MatriculaCreate(SQLModel):
    estudiante_id: int
    curso_id: int


class MatriculaUpdate(SQLModel):
    nota_final: Optional[float] = Field(ge=0, le=5)
    aprobado: Optional[bool] = None




#MODELOS CON RELACIONES

class EstudianteconCursos(EstudianteBase):
    id: int
    cursos: list[CursoBase]=[]

class CursosConEstudiantes(CursoBase):
    id: int
    estudiantes: list[EstudianteBase]
    profesore: ProfesorBase
    departamento: DepartamentoBase

class ProfesorConCursos(ProfesorBase):
    id:int
    cursos: list[CursoBase]=[]
    departamento: DepartamentoBase

class DepartamentoCompleto(DepartamentoBase):
    id:int
    profesores: list[ProfesorBase]=[]
    cursos: list[CursoBase]=[]


