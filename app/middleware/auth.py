import datetime
import json

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.security import verify_session_token


class SessionTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "PATCH" and request.url.path.startswith("/api/perfiles/"):
            raw_token = request.headers.get("X-Session-Token")
            if not raw_token:
                return Response(
                    content=json.dumps({"error": "X-Session-Token header required"}),
                    status_code=401,
                    media_type="application/json",
                )

            path_parts = request.url.path.rstrip("/").split("/")
            public_id = path_parts[-1] if path_parts else None

            if not public_id:
                return Response(
                    content=json.dumps({"error": "Acceso denegado"}),
                    status_code=403,
                    media_type="application/json",
                )

            from app.models.perfil import Perfil as PerfilModel

            collection = PerfilModel.get_motor_collection()
            doc = await collection.find_one({"publicId": public_id})

            if not doc or not doc.get("sessionToken") or not doc.get("sessionTokenSalt"):
                return Response(
                    content=json.dumps({"error": "Acceso denegado"}),
                    status_code=403,
                    media_type="application/json",
                )

            expiry = doc.get("sessionExpiry")
            if expiry and expiry < datetime.datetime.utcnow():
                return Response(
                    content=json.dumps({"error": "Session expired"}),
                    status_code=403,
                    media_type="application/json",
                )

            valid = verify_session_token(raw_token, doc["sessionToken"], doc["sessionTokenSalt"])
            if not valid:
                return Response(
                    content=json.dumps({"error": "Acceso denegado"}),
                    status_code=403,
                    media_type="application/json",
                )

        return await call_next(request)
