import argparse
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

from app.core.exceptions import ETLError, IntegrityCheckError, SSRFBlockedError
from app.db.mongodb import close_db, connect_db
from app.utils.etl.factory import ParserFactory
from app.utils.etl.integrity import ETLIntegrity
from app.api.carreras.repository import CarreraRepository
from app.models.data_fuente_auditoria import DataFuenteAuditoria


async def run(source: str, url: str, dry_run: bool, expected_hash: str | None) -> None:
    ETLIntegrity.validate_url(url)

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=60)
        resp.raise_for_status()

    actual_hash = ETLIntegrity.check_hash(resp.content, expected_hash)

    parser = ParserFactory.get_parser(source)
    records = parser.parse(resp.content)

    print(f"Parsed {len(records)} records from {source}")

    await connect_db()

    try:
        if not dry_run:
            repo = CarreraRepository()
            for record in records:
                await repo.upsert(record)
            print(f"Upserted {len(records)} records")
        else:
            print("Dry run — no writes performed")

        await DataFuenteAuditoria(
            fuente=url,
            totalRegistros=len(records),
            hash=actual_hash,
            dryRun=dry_run,
        ).insert()
    finally:
        await close_db()


def main() -> None:
    parser = argparse.ArgumentParser(description="EcuRoad ETL runner")
    parser.add_argument("--source", required=True, choices=ParserFactory.available_sources())
    parser.add_argument("--url", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--expected-hash", default=None)
    args = parser.parse_args()

    try:
        asyncio.run(
            run(
                source=args.source,
                url=args.url,
                dry_run=args.dry_run,
                expected_hash=args.expected_hash,
            )
        )
    except SSRFBlockedError as exc:
        print(f"SSRF blocked: {exc}", file=sys.stderr)
        sys.exit(1)
    except IntegrityCheckError as exc:
        print(f"Hash mismatch: {exc}", file=sys.stderr)
        sys.exit(1)
    except ETLError as exc:
        print(f"ETL error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
