# Importa tipos de columnas y relaciones
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

# Importa la Base declarativa desde database.py (¡única fuente!)
from database import Base

# -------------------------------
# Modelo de la tabla 'usuario'
# -------------------------------

class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    apellidos = Column(String)
    conectado = Column(Boolean, default=False)

# -------------------------------
# Modelo de la tabla 'auditoria'
# -------------------------------

# -------------------------------
# Modelo de la tabla 'personal'
# -------------------------------
class Personal(Base):
    __tablename__ = "personal"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String)
    num_tarjeta = Column(String)
    nombre = Column(String)
    apellidos = Column(String)
    carea_fk = Column(Integer, ForeignKey("carea.id"))   # Relación con área

# -------------------------------
# Modelo de la tabla 'carea'
# -------------------------------
class Carea(Base):
    __tablename__ = "carea"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    codigo = Column(String)

# -------------------------------
# Modelo de la tabla 'control_asistencia'
# -------------------------------
class ControlAsistencia(Base):
    __tablename__ = "control_asistencia"

    id = Column(Integer, primary_key=True, index=True)
    id_person = Column(Integer, ForeignKey("personal.id"))  # Relación con personal

# -------------------------------
# Modelo de la tabla 'incidencias_asistencia'
# -------------------------------
class IncidenciasAsistencia(Base):
    __tablename__ = "incidencias_asistencia"

    id = Column(Integer, primary_key=True, index=True)
    control_asistencia_fk = Column(Integer, ForeignKey("control_asistencia.id"))
    marca_entrada = Column(DateTime)   # Hora de entrada
    fecha = Column(Date)               # Fecha (DATE en la BD)
