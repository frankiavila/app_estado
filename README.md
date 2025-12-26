# Sistema de Reportes de Asistencia — FastAPI

Este proyecto es una aplicación web desarrollada con **FastAPI**, diseñada para gestionar usuarios y generar reportes de asistencia de forma eficiente, clara y profesional.

---

## 🚀 Tecnologías utilizadas

- **Python 3.11+**
- **FastAPI**
- **Uvicorn**
- **Jinja2** (para plantillas HTML)
- **SQLAlchemy** (ORM para base de datos)
- **SQLite** (base de datos local)
- **HTML + CSS** (interfaz de usuario)
- **VS Code** (entorno de desarrollo)

---

## 🛠️ Instalación y ejecución local

python -m venv venv
venv\Scripts\activate   # En Windows

pip install -r requirements.txt

uvicorn main:app --reload

 http://127.0.0.1:8000

 app_estado/
├── main.py                  # Punto de entrada de la app
├── database.py              # Conexión y configuración de la base de datos
├── models.py                # Definición de modelos SQLAlchemy
├── schemas.py               # Esquemas Pydantic para validación
├── templates/               # Plantillas HTML (Jinja2)
│   ├── base.html
│   ├── usuarios.html
│   └── reporte_asistencia.html
├── static/                  # Archivos estáticos (CSS, JS)
│   └── style.css
├── .gitignore               # Archivos a ignorar por Git
├── requirements.txt         # Dependencias del proyecto
└── README.md                # Este archivo



### 1. Clona el repositorio

```bash
git clone https://github.com/frankiavila/app_estado.git
cd app_estado
