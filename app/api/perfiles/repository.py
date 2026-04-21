from app.models.perfil import Perfil


class PerfilRepository:
    async def create(self, data: dict) -> Perfil:
        perfil = Perfil(**data)
        await perfil.insert()
        return perfil

    async def get_by_public_id(self, public_id: str) -> Perfil | None:
        return await Perfil.find_one(Perfil.publicId == public_id)

    async def update(self, public_id: str, data: dict) -> Perfil | None:
        perfil = await self.get_by_public_id(public_id)
        if perfil is None:
            return None
        update_data = {k: v for k, v in data.items() if v is not None}
        if update_data:
            await perfil.set(update_data)
        return perfil

    async def get_with_token(self, public_id: str) -> dict | None:
        collection = Perfil.get_motor_collection()
        doc = await collection.find_one({"publicId": public_id})
        return doc
