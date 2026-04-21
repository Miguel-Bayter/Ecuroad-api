import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mangum import Mangum
from main import create_app

app = create_app()

# Mangum adapts FastAPI (ASGI) to AWS Lambda / Vercel serverless handler.
# lifespan="off" disables startup/shutdown events — DB init is handled lazily
# via the ensure_db middleware on each request instead.
handler = Mangum(app, lifespan="off")
