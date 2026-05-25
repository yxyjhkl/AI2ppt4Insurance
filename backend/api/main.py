import sys
import os
import re
import logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .routes import convert, generate, templates, ai, media, export_route, progress


class APIKeyFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = re.sub(
                r'(api_key|api[-_]?key|secret|token|apikey)["\']?\s*[:=]\s*["\']?([^\s"\'&]{0,4})([^\s"\'&]+)([^\s"\'&]{0,4})["\']?',
                r'\1\2****\4', record.msg, flags=re.IGNORECASE
            )
            record.msg = re.sub(
                r'(Authorization:\s*Bearer\s+)(\S{0,6})(\S+?)(\S{0,4})',
                r'\1\2****\4', record.msg
            )
            record.msg = re.sub(
                r'(sk-[^\s"\'&]{0,4})[^\s"\'&]+([^\s"\'&]{0,4})',
                r'\1****\2', record.msg
            )
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
for handler in logging.root.handlers:
    handler.addFilter(APIKeyFilter())
logger = logging.getLogger(__name__)

app = FastAPI(title="AI PPT Desktop Backend", version="1.0.0")

CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

if os.environ.get("APP_DEV_MODE", "0") == "1":
    CORS_ORIGINS.append("file://")

# Web deployment mode: allow all origins when DEPLOY_MODE=web
if os.environ.get("DEPLOY_MODE", "") == "web":
    CORS_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
    return response

app.include_router(convert.router, prefix="/api/v1/convert", tags=["convert"])
app.include_router(generate.router, prefix="/api/v1/generate", tags=["generate"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(media.router, prefix="/api/v1/media", tags=["media"])
app.include_router(export_route.router, prefix="/api/v1", tags=["export"])
app.include_router(progress.router, prefix="/api/v1", tags=["progress"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
