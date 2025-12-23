from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Declarative base única para todos los modelos
Base = declarative_base()

# Conexión a la BD de usuarios (secgrehu_novatec)
SQLALCHEMY_DATABASE_URL1 = "postgresql://postgres:postgres@10.25.16.14:5432/secgrehu_novatec"
engine1 = create_engine(SQLALCHEMY_DATABASE_URL1)
SessionLocal1 = sessionmaker(autocommit=False, autoflush=False, bind=engine1)

# Conexión a la BD de asistencia (grehu_novatec)
SQLALCHEMY_DATABASE_URL2 = "postgresql://postgres:postgres@10.25.16.14:5432/grehu_novatec"
engine2 = create_engine(SQLALCHEMY_DATABASE_URL2)
SessionLocal2 = sessionmaker(autocommit=False, autoflush=False, bind=engine2)
