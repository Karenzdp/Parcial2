from fastapi import APIRouter, HTTPException
from sqlmodel import SessionDep
from db import create_tables
from models import (
    Curso,CursoCreate, CursoUpdate, CursosConEstudiantes,
        Profesor, Departamento, Estudiante
)
