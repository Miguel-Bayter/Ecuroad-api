from beanie import Document
from pydantic import Field
from typing import Optional
import datetime


class DataFuenteAuditoria(Document):
    fuente: str
    fechaIngesta: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    totalRegistros: int
    hash: str
    operador: str = "system"
    dryRun: bool = False

    class Settings:
        name = "data_fuente_auditoria"
