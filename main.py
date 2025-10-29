from fastapi import FastAPI
from db import create_tables
from Parcial2 import estudiantes, departamento, matriculas
from Parcial2 import curso, profesor
app = FastAPI(
    title="Universidad",
    description="API REST para gestión de cursos y estudiantes con FastAPI y SQLModel",
    version="1.0.0"
)

create_tables()

app.include_router(estudiantes.router, tags=["Estudiantes"], prefix="/estudiantes")
app.include_router(curso.router, tags=["Cursos"], prefix="/cursos")
app.include_router(departamento.router, tags=["Departamento"], prefix="/departamentos")
app.include_router(profesor.router, tags=["Profesor"], prefix="/profesores")
app.include_router(matriculas.router, tags=["Matriculas"], prefix="/matriculas")