import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreatePerfilRequest(BaseModel):
    ciudad: str = Field(..., min_length=2, max_length=100, pattern=r"^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$")
    estrato: int = Field(..., ge=1, le=6)
    presupuesto: int = Field(..., ge=0, le=50_000_000)
    intereses: list[str] = Field(default_factory=list)
    tipoCarrera: str = Field(default="cualquiera", pattern=r"^(universitaria|tecnica|tecnologica|cualquiera)$")


class UpdatePerfilRequest(BaseModel):
    ciudad: Optional[str] = Field(None, min_length=2, max_length=100, pattern=r"^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$")
    estrato: Optional[int] = Field(None, ge=1, le=6)
    presupuesto: Optional[int] = Field(None, ge=0, le=50_000_000)
    intereses: Optional[list[str]] = None
    tipoCarrera: Optional[str] = Field(None, pattern=r"^(universitaria|tecnica|tecnologica|cualquiera)$")


class PerfilResponse(BaseModel):
    publicId: str
    ciudad: str
    estrato: int
    presupuesto: int
    intereses: list[str]
    tipoCarrera: str
    sessionExpiry: Optional[datetime.datetime] = None


class CreatePerfilResponse(BaseModel):
    perfil: PerfilResponse
    sessionToken: str  # returned ONCE on creation only
