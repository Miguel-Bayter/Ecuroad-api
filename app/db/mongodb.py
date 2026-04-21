from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from config import get_settings

_client: AsyncIOMotorClient | None = None
_initialized: bool = False


async def connect_db() -> None:
    global _client, _initialized
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    from app.models.carrera import Carrera
    from app.models.perfil import Perfil
    from app.models.audit_log import AuditLog
    from app.models.data_fuente_auditoria import DataFuenteAuditoria

    await init_beanie(
        database=_client.get_default_database(),
        document_models=[Carrera, Perfil, AuditLog, DataFuenteAuditoria],
    )
    _initialized = True


async def ensure_initialized() -> None:
    """Lazy init for serverless environments where lifespan may not fire."""
    if not _initialized:
        await connect_db()


async def close_db() -> None:
    if _client:
        _client.close()
