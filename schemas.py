from pydantic import BaseModel

class UsuarioSchema(BaseModel):
    id: int
    nombre: str | None
    apellidos: str | None
    conectado: bool | None

    class Config:
        from_attributes = True

