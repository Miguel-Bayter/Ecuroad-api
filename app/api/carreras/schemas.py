import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CarreraResponse(BaseModel):
    nombre: str
    slug: str
    descripcion: str
    categoria: str
    tipo: str
    duracionSemestres: int
    costoSemestre: int
    salarioEntrada: int
    salarioMedio: int
    salarioMediana: Optional[int] = None
    empleabilidad: float
    tasaEmpleabilidad12m: Optional[float] = None
    demandaPorRegion: dict[str, float]
    universidades: list[str]
    habilidadesRequeridas: list[str]
    tags: list[str]
    proyeccion2030: Optional[str] = None
    acreditadaAltaCalidad: bool
    ultimaActualizacion: datetime.datetime
    cineCode: Optional[str] = None


class CarreraListResponse(BaseModel):
    items: list[CarreraResponse]
    total: int
    page: int
    limit: int


class RecomendacionesRequest(BaseModel):
    ciudad: str = Field(..., max_length=100, pattern=r"^[A-Za-záéíóúÁÉÍÓÚñÑ\s]+$")
    estrato: int = Field(..., ge=1, le=6)
    presupuesto: int = Field(..., ge=0, le=50_000_000)
    intereses: list[str] = Field(default_factory=list)
    tipoCarrera: str = Field(default="cualquiera")
    limite: int = Field(default=10, ge=1, le=20)


class ScoredCarreraResponse(CarreraResponse):
    score: float
