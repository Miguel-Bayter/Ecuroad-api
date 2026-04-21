import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class Carrera(Document):
    nombre: str
    slug: Indexed(str, unique=True)  # type: ignore[valid-type]
    descripcion: str
    categoria: Indexed(str)  # type: ignore[valid-type]
    tipo: Indexed(str)  # type: ignore[valid-type]
    duracionSemestres: int
    costoSemestre: int
    salarioEntrada: int
    salarioMedio: int
    salarioMediana: Optional[int] = None
    empleabilidad: float  # 0-100
    tasaEmpleabilidad12m: Optional[float] = None
    demandaPorRegion: dict[str, float] = Field(default_factory=dict)
    universidades: list[str] = Field(default_factory=list)
    habilidadesRequeridas: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    proyeccion2030: Optional[str] = None
    acreditadaAltaCalidad: bool = False
    ultimaActualizacion: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow
    )
    cineCode: Optional[str] = None

    # Internal — excluded from client-facing serialization
    sniesCode: Optional[str] = Field(None, exclude=True)
    fuenteSalario: str = Field("manual", exclude=True)
    fuenteDemanda: str = Field("manual", exclude=True)
    verificado: bool = Field(False, exclude=True)
    visitas: int = Field(0, exclude=True)

    def to_public(self) -> dict:
        return self.model_dump(
            exclude={
                "sniesCode",
                "fuenteSalario",
                "fuenteDemanda",
                "verificado",
                "visitas",
                "id",
                "revision_id",
            }
        )

    class Settings:
        name = "carreras"
        indexes = [
            [("slug", 1)],
            [("categoria", 1)],
            [("tipo", 1)],
        ]
