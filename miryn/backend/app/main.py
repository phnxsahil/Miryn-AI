from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from time import perf_counter
from uuid import uuid4
import sentry_sdk
from sqlalchemy import text
from sentry_sdk.integrations.fastapi import FastApiIntegration
from app.config import settings
from app.core.database import get_sql_session
from app.core.cache import redis_client
from app.api import auth, chat, identity, onboarding, llm, notifications, tools, memory, import_data
from app.api.analytics import router as analytics_router
from app.core.rate_limit import RateLimitMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        integrations=[FastApiIntegration()],
    )

app = FastAPI(
    title="Miryn API",
    description="Context-aware AI companion with persistent memory",
    version="0.1.0",
)

allow_origins = []
if settings.FRONTEND_URL and settings.FRONTEND_URL.strip():
    allow_origins.append(settings.FRONTEND_URL.strip().rstrip("/"))

if settings.BACKEND_URL and settings.BACKEND_URL.strip():
    allow_origins.append(settings.BACKEND_URL.strip().rstrip("/"))

allow_origins.extend([
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
])
allow_origins = list(dict.fromkeys(allow_origins))

app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(identity.router)
app.include_router(onboarding.router)
app.include_router(llm.router)
app.include_router(notifications.router)
app.include_router(tools.router)
app.include_router(memory.router)
app.include_router(import_data.router)
app.include_router(analytics_router)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    started_at = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        logger.exception(
            "request_failed request_id=%s method=%s path=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Handle uncaught exceptions by returning a 500 JSON response and preserve CORS headers when the request origin is allowed.

    Parameters:
        request (Request): The incoming HTTP request; its Origin header is inspected to determine CORS headers.
        exc (Exception): The exception instance that was raised.

    Returns:
        JSONResponse: HTTP response with status code 500 and body {"detail": "Internal server error"}. If the request Origin is in the application's allowed origins, the response includes `Access-Control-Allow-Origin` and `Access-Control-Allow-Credentials` headers.
    """
    logger.exception(
        "Unhandled exception request_id=%s method=%s path=%s",
        getattr(request.state, "request_id", "unknown"),
        request.method,
        request.url.path,
        exc_info=exc,
    )
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in allow_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    if getattr(request.state, "request_id", None):
        headers["X-Request-ID"] = request.state.request_id
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=headers,
    )


@app.get("/")
def root():
    return {"message": "Miryn API v0.1.0"}


@app.get("/health")
async def health_check():
    checks = {}
    try:
        with get_sql_session() as s:
            s.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {str(e)[:50]}"
    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)[:50]}"
    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks, "version": "0.1.0"}
