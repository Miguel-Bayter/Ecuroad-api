from app.models.carrera import Carrera
from beanie.operators import Set


class CarreraRepository:
    async def get_all(
        self,
        categoria: str | None = None,
        tipo: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Carrera], int]:
        filters: dict = {}
        if categoria:
            filters["categoria"] = categoria
        if tipo:
            filters["tipo"] = tipo

        query = Carrera.find(filters)
        total = await query.count()
        items = await query.skip((page - 1) * limit).limit(limit).to_list()
        return items, total

    async def get_by_slug(self, slug: str) -> Carrera | None:
        return await Carrera.find_one(Carrera.slug == slug)

    async def increment_visits(self, slug: str) -> None:
        await Carrera.find_one({"slug": slug}).update({"$inc": {"visitas": 1}})

    async def upsert(self, data: dict) -> Carrera:
        existing = await Carrera.find_one(Carrera.slug == data["slug"])
        if existing:
            await existing.update(Set(data))
            return existing
        carrera = Carrera(**data)
        await carrera.insert()
        return carrera
