import datetime
from typing import Optional

from beanie import Document
from pydantic import Field
from ulid import ULID


class Perfil(Document):
    publicId: str = Field(default_factory=lambda: str(ULID()))
    ciudad: str
    estrato: int  # 1-6
    presupuesto: int
    intereses: list[str] = Field(default_factory=list)
    tipoCarrera: str = "cualquiera"
    sessionToken: Optional[str] = Field(None, exclude=True)
    sessionTokenSalt: Optional[str] = Field(None, exclude=True)
    sessionExpiry: Optional[datetime.datetime] = Field(
        default_factory=lambda: datetime.datetime.utcnow() + datetime.timedelta(days=90)
    )
    createdAt: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    def to_public(self) -> dict:
        return self.model_dump(
            exclude={"sessionToken", "sessionTokenSalt", "id", "revision_id"}
        )

    class Settings:
        name = "perfiles"
