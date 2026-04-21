from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.perfiles.schemas import (
    CreatePerfilRequest,
    CreatePerfilResponse,
    PerfilResponse,
    UpdatePerfilRequest,
)
from app.api.perfiles.service import PerfilService
from app.core.exceptions import PerfilNotFound

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def get_service() -> PerfilService:
    from app.api.perfiles.repository import PerfilRepository

    return PerfilService(PerfilRepository())


@router.post("/", response_model=CreatePerfilResponse)
@limiter.limit("5/hour")
async def create_perfil(
    request: Request,
    body: CreatePerfilRequest,
    service: PerfilService = Depends(get_service),
) -> CreatePerfilResponse:
    perfil, raw_token = await service.create_perfil(body)
    return CreatePerfilResponse(
        perfil=PerfilResponse(**perfil.to_public()),
        sessionToken=raw_token,
    )


@router.get("/{id}", response_model=PerfilResponse)
async def get_perfil(
    id: str,
    service: PerfilService = Depends(get_service),
) -> PerfilResponse:
    try:
        perfil = await service.get_perfil(id)
        return PerfilResponse(**perfil.to_public())
    except PerfilNotFound:
        raise HTTPException(status_code=404, detail=f"Perfil '{id}' not found")


@router.patch("/{id}", response_model=PerfilResponse)
async def update_perfil(
    id: str,
    body: UpdatePerfilRequest,
    service: PerfilService = Depends(get_service),
) -> PerfilResponse:
    try:
        perfil = await service.update_perfil(id, body)
        return PerfilResponse(**perfil.to_public())
    except PerfilNotFound:
        raise HTTPException(status_code=404, detail=f"Perfil '{id}' not found")
