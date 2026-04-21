from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.carreras.schemas import (
    CarreraListResponse,
    CarreraResponse,
    RecomendacionesRequest,
    ScoredCarreraResponse,
)
from app.api.carreras.service import CarreraService
from app.core.exceptions import CarreraNotFound

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def get_service() -> CarreraService:
    return CarreraService()


@router.get("/", response_model=CarreraListResponse)
async def list_careers(
    categoria: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: CarreraService = Depends(get_service),
) -> CarreraListResponse:
    return await service.list_careers(categoria=categoria, tipo=tipo, page=page, limit=limit)


@router.post("/recomendaciones", response_model=list[ScoredCarreraResponse])
@limiter.limit("30/15minutes")
async def recommend_careers(
    request: Request,
    body: RecomendacionesRequest,
    service: CarreraService = Depends(get_service),
) -> list[ScoredCarreraResponse]:
    scored = await service.recommend_careers(body)
    results = []
    for sc in scored:
        public = sc.carrera.to_public()
        results.append(ScoredCarreraResponse(**public, score=sc.score))
    return results


@router.get("/{slug}/stats")
async def career_stats(
    slug: str,
    service: CarreraService = Depends(get_service),
) -> dict:
    try:
        return await service.career_stats(slug)
    except CarreraNotFound:
        raise HTTPException(status_code=404, detail=f"Carrera '{slug}' not found")


@router.get("/{slug}", response_model=CarreraResponse)
async def get_career(
    slug: str,
    service: CarreraService = Depends(get_service),
) -> CarreraResponse:
    try:
        carrera = await service.get_career(slug)
        return CarreraResponse(**carrera.to_public())
    except CarreraNotFound:
        raise HTTPException(status_code=404, detail=f"Carrera '{slug}' not found")
