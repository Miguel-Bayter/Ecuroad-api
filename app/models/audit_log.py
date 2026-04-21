from beanie import Document
from pydantic import Field
from typing import Optional
import datetime


class AuditLog(Document):
    event: str
    ip: str
    path: str
    status_code: int
    details: Optional[dict] = None
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    class Settings:
        name = "audit_logs"
