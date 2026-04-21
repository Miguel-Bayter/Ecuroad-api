from app.api.perfiles.repository import PerfilRepository
from app.api.perfiles.schemas import CreatePerfilRequest, UpdatePerfilRequest
from app.core.exceptions import PerfilNotFound
from app.models.perfil import Perfil
from app.utils.security import generate_session_token, hash_session_token


class PerfilService:
    def __init__(self, repo: PerfilRepository) -> None:
        self.repo = repo

    async def create_perfil(self, data: CreatePerfilRequest) -> tuple[Perfil, str]:
        raw_token = generate_session_token()
        hashed, salt = hash_session_token(raw_token)
        perfil_data = data.model_dump()
        perfil_data["sessionToken"] = hashed
        perfil_data["sessionTokenSalt"] = salt
        perfil = await self.repo.create(perfil_data)
        return perfil, raw_token

    async def get_perfil(self, public_id: str) -> Perfil:
        perfil = await self.repo.get_by_public_id(public_id)
        if perfil is None:
            raise PerfilNotFound(public_id)
        return perfil

    async def update_perfil(self, public_id: str, data: UpdatePerfilRequest) -> Perfil:
        perfil = await self.repo.update(public_id, data.model_dump(exclude_unset=True))
        if perfil is None:
            raise PerfilNotFound(public_id)
        return perfil
