from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from db import SessionDep
from models import (
    Estudiante, EstudianteCreate, EstudianteUpdate,
    EstudianteConCursos, Curso
)
import re

