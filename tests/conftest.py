import pytest
from httpx import AsyncClient, ASGITransport
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from app.models.carrera import Carrera
from app.models.perfil import Perfil
from app.models.audit_log import AuditLog
from app.models.data_fuente_auditoria import DataFuenteAuditoria


@pytest.fixture
async def db():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client.get_database("test_db"),
        document_models=[Carrera, Perfil, AuditLog, DataFuenteAuditoria],
    )
    yield
    await Carrera.delete_all()
    await Perfil.delete_all()
    await AuditLog.delete_all()
    await DataFuenteAuditoria.delete_all()


@pytest.fixture
async def client(db):
    from main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
