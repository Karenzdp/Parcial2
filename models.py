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



#
class Estudiante(EstudianteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cursos: list["Curso"] = Relationship(back_populates="estudiantes", link_model=Matricula)

class Departamento(CursoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    profesores: list["Profesor"] = Relationship(back_populates="cursos")
    cursos: list["Curso"] = Relationship(back_populates="profesores")


