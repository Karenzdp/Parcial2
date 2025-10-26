from operator import index

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
