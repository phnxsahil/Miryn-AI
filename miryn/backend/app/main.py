from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api import auth, chat, identity, onboarding, llm, notifications, tools
from app.core.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="Miryn API",
    description="Context-aware AI companion with persistent memory",
    version="0.1.0",
)

allow_origins = []
if settings.FRONTEND_URL and settings.FRONTEND_URL.strip():
    allow_origins.append(settings.FRONTEND_URL.strip())

allow_origins.extend([
    "http://localhost:3000",
    "http://127.0.0.1:3000",
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Ensure CORS headers are present even on unhandled 500 errors."""
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in allow_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=headers,
    )


@app.get("/")
def root():
    return {"message": "Miryn API v0.1.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
