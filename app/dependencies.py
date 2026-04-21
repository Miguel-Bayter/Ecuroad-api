import hashlib
import hmac

from fastapi import Header, HTTPException

from app.api.carreras.repository import CarreraRepository
from app.api.carreras.service import CarreraService
from app.api.perfiles.repository import PerfilRepository
from app.api.perfiles.service import PerfilService
from config import get_settings


def get_carrera_service() -> CarreraService:
    return CarreraService(CarreraRepository())


def get_perfil_service() -> PerfilService:
    return PerfilService(PerfilRepository())


async def verify_admin_api_key(x_api_key: str = Header(...)) -> str:
    settings = get_settings()
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    if not hmac.compare_digest(key_hash, settings.ADMIN_API_KEY_HASH):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key
