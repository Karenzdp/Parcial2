# 🎓 Sistema de Gestión Universitaria

API REST para la gestión de estudiantes, profesores, cursos, departamentos y matrículas universitarias.

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/sistema-gestion-universitaria.git
cd sistema-gestion-universitaria
```

### 2. Crear y activar entorno virtual

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar el servidor

```bash
uvicorn app.main:app --reload
```

---

## 📍 Acceso a la API

- **API Base:** `http://localhost:8000`
- **Documentación interactiva (Swagger UI):** `http://localhost:8000/docs`
- **Documentación alternativa (ReDoc):** `http://localhost:8000/redoc`

---

## 🛠️ Tecnologías

- **Python 3.10+**
- **FastAPI** - Framework web
- **SQLModel** - ORM
- **Pydantic** - Validación de datos
- **SQLite** - Base de datos (por defecto)
- **Uvicorn** - Servidor ASGI

---

## 📁 Estructura del Proyecto

```
proyecto/
│
├── app/
│   ├── main.py              # Punto de entrada
│   ├── db.py                # Configuración BD
│   ├── models.py            # Modelos de datos
│   │
│   └── routers/
│       ├── estudiantes.py
│       ├── profesores.py
│       ├── cursos.py
│       ├── departamentos.py
│       └── matriculas.py
│
├── requirements.txt
└── README.md
```

---

## 📝 Endpoints Principales

### Estudiantes - `/estudiantes`
- `POST /` - Crear estudiante
- `GET /` - Listar todos
- `GET /{id}` - Obtener por ID
- `PUT /{id}` - Actualizar
- `DELETE /{id}` - Desactivar (elimina matrículas automáticamente)
- `GET /buscar/cedula/{cedula}` - Buscar por cédula
- `GET /buscar/nombre?nombre={nombre}` - Buscar por nombre

### Profesores - `/profesores`
- `POST /` - Crear profesor
- `GET /` - Listar todos
- `GET /{id}` - Obtener por ID
- `PUT /{id}` - Actualizar
- `DELETE /{id}` - Desactivar
- `GET /buscar/cedula/{cedula}` - Buscar por cédula
- `GET /buscar/activos` - Listar activos

### Cursos - `/cursos`
- `POST /` - Crear curso
- `GET /{id}` - Obtener por ID
- `PUT /{id}` - Actualizar
- `DELETE /{id}` - Desactivar (elimina matrículas automáticamente)
- `GET /buscar/codigo/{codigo}` - Buscar por código
- `GET /buscar/nombre?nombre={nombre}` - Buscar por nombre

### Departamentos - `/departamentos`
- `POST /` - Crear departamento
- `GET /{id}` - Obtener por ID
- `PUT /{id}` - Actualizar
- `DELETE /{id}` - Eliminar
- `GET /listar/todos` - Listar todos

### Matrículas - `/matriculas`
- `POST /` - Matricular estudiante en curso
- `DELETE /{estudiante_id}/{curso_id}` - Desmatricular
- `GET /estudiante/{estudiante_id}` - Matrículas de estudiante
- `GET /curso/{curso_id}` - Matrículas de curso

---

## 💡 Notas Importantes

### Eliminación en Cascada
- **Estudiantes:** Al desactivar un estudiante, se eliminan automáticamente todas sus matrículas
- **Cursos:** Al desactivar un curso, se eliminan automáticamente todas las matrículas de sus estudiantes
- **Profesores:** No se pueden desactivar si tienen cursos asignados
- **Departamentos:** No se pueden eliminar si tienen profesores o cursos

### Búsquedas
- Todas las búsquedas por texto son **case-insensitive** (no distinguen mayúsculas/minúsculas)

### Validaciones
- Cédulas: 5-12 dígitos
- Emails: Formato válido y únicos
- Semestre: Entre 1 y 12
- Créditos: Entre 1 y 6
- Códigos de departamento: 2-5 caracteres alfanuméricos

---

## 🧪 Probar la API

Una vez el servidor esté corriendo, visita:
```
http://localhost:8000/docs
```

Allí encontrarás la documentación interactiva donde puedes probar todos los endpoints directamente desde el navegador.

---

