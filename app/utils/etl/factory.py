from app.utils.etl.base import BaseParser
from app.utils.etl.snies import SNIESCSVParser
from app.utils.etl.ole import OLEExcelParser

_REGISTRY: dict[str, type[BaseParser]] = {
    "snies": SNIESCSVParser,
    "ole": OLEExcelParser,
}


class ParserFactory:
    @staticmethod
    def get_parser(source: str) -> BaseParser:
        cls = _REGISTRY.get(source.lower())
        if cls is None:
            raise ValueError(f"Unknown ETL source: '{source}'. Valid: {list(_REGISTRY.keys())}")
        return cls()

    @staticmethod
    def available_sources() -> list[str]:
        return list(_REGISTRY.keys())
