# Sentry Setup

## Backend

1. Create a Sentry project for the backend.
2. Copy the DSN.
3. In `miryn/backend/.env`, add:

```env
SENTRY_DSN=your_backend_dsn
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=0.1
```

4. Restart the backend.

## Frontend

1. Create a Sentry project for the frontend.
2. Copy the DSN.
3. In `miryn/frontend/.env.local`, add:

```env
NEXT_PUBLIC_SENTRY_DSN=your_frontend_dsn
NEXT_PUBLIC_SENTRY_ENVIRONMENT=development
NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE=0.1
```

4. Restart the frontend.

## Local Redis

Run:

```powershell
cd miryn\backend
.\start-redis.ps1
```

Expected Redis check result:

```text
PONG
```
