from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.carreras.repository import CarreraRepository
from app.core.exceptions import ETLError, IntegrityCheckError, SSRFBlockedError
from app.dependencies import verify_admin_api_key
from app.models.data_fuente_auditoria import DataFuenteAuditoria
from app.utils.etl.factory import ParserFactory
from app.utils.etl.integrity import ETLIntegrity

router = APIRouter()


class ETLRunRequest(BaseModel):
    source: str
    url: str
    dry_run: bool = False
    expected_hash: Optional[str] = None


@router.post("/etl/run")
async def etl_run(
    body: ETLRunRequest,
    _: str = Depends(verify_admin_api_key),
):
    try:
        ETLIntegrity.validate_url(body.url)
    except SSRFBlockedError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(body.url, timeout=60)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream fetch failed: {exc}")

    try:
        actual_hash = ETLIntegrity.check_hash(resp.content, body.expected_hash)
    except IntegrityCheckError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        parser = ParserFactory.get_parser(body.source)
        records = parser.parse(resp.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ETLError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    inserted = 0
    if not body.dry_run:
        repo = CarreraRepository()
        for record in records:
            await repo.upsert(record)
            inserted += 1

    await DataFuenteAuditoria(
        fuente=body.url,
        totalRegistros=len(records),
        hash=actual_hash,
        dryRun=body.dry_run,
    ).insert()

    return {
        "source": body.source,
        "totalRecords": len(records),
        "dryRun": body.dry_run,
        "hash": actual_hash,
    }
