from app.api.carreras.repository import CarreraRepository
from app.api.carreras.schemas import (
    CarreraListResponse,
    CarreraResponse,
    RecomendacionesRequest,
)
from app.core.exceptions import CarreraNotFound
from app.models.carrera import Carrera
from app.utils.scoring import ScoredCarrera, rank_careers


class CarreraService:
    def __init__(self, repo: CarreraRepository | None = None) -> None:
        self.repo = repo or CarreraRepository()

    async def list_careers(
        self,
        categoria: str | None = None,
        tipo: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> CarreraListResponse:
        items, total = await self.repo.get_all(
            categoria=categoria, tipo=tipo, page=page, limit=limit
        )
        return CarreraListResponse(
            items=[CarreraResponse(**c.to_public()) for c in items],
            total=total,
            page=page,
            limit=limit,
        )

    async def get_career(self, slug: str) -> Carrera:
        carrera = await self.repo.get_by_slug(slug)
        if not carrera:
            raise CarreraNotFound(f"Carrera '{slug}' not found")
        await self.repo.increment_visits(slug)
        return carrera

    async def recommend_careers(
        self, request: RecomendacionesRequest
    ) -> list[ScoredCarrera]:
        all_items, _ = await self.repo.get_all(limit=1000)
        perfil = request.model_dump()
        return rank_careers(all_items, perfil, limit=request.limite)

    async def career_stats(self, slug: str) -> dict:
        # Raw fetch needed because visitas is an excluded field
        raw = await Carrera.get_motor_collection().find_one(
            {"slug": slug}, {"visitas": 1, "_id": 0}
        )
        if raw is None:
            raise CarreraNotFound(f"Carrera '{slug}' not found")
        return {"slug": slug, "visitas": raw.get("visitas", 0)}
