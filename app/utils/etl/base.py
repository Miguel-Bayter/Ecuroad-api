from abc import ABC, abstractmethod


class BaseParser(ABC):
    @abstractmethod
    def parse(self, data: bytes) -> list[dict]:
        """Parse raw bytes into a list of record dicts."""
        ...

    @abstractmethod
    def validate_record(self, record: dict) -> bool:
        """Return True if the record has required fields and is active."""
        ...
