#!/usr/bin/env python3
"""One API process + one solo Celery worker with embedded beat.

Any child exit fails the container, so Render can restart both. Termination
signals reach all process groups, including the embedded beat child. Startup
runs repo migrations on a direct Neon URL, serialized with an advisory lock.
"""
import os
import signal
import subprocess
import sys
import time
from urllib.parse import urlsplit

children = []
stopping = False


def log(message):
    print(f"[render-start] {message}", flush=True)


def handle_stop(signum, frame):
    global stopping
    stopping = True
    for child in children:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def spawn(argv, env=None):
    child = subprocess.Popen(argv, env=env, start_new_session=True)
    children.append(child)
    # Handle a termination arriving between Popen and registration.
    if stopping:
        handle_stop(signal.SIGTERM, None)
    return child


def shutdown():
    handle_stop(signal.SIGTERM, None)
    deadline = time.monotonic() + 20
    while any(child.poll() is None for child in children) and time.monotonic() < deadline:
        time.sleep(0.2)
    for child in children:
        # Kill the whole group even if its group leader already exited.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    for child in children:
        child.wait()


def validate_environment():
    required = ["DATABASE_URL", "MIGRATION_DATABASE_URL", "REDIS_URL", "SECRET_KEY",
                "ENCRYPTION_KEY", "GEMINI_API_KEY", "FRONTEND_URL", "BACKEND_URL"]
    missing = [key for key in required if not os.environ.get(key, "").strip()]
    if missing:
        raise RuntimeError("Missing environment variables: " + ", ".join(missing))
    direct = urlsplit(os.environ["MIGRATION_DATABASE_URL"])
    if direct.scheme != "postgresql" or not direct.hostname or "-pooler." in direct.hostname:
        raise RuntimeError("MIGRATION_DATABASE_URL must be a direct postgresql:// Neon URL")
    from app.core.encryption import encryption_available
    if not encryption_available():
        raise RuntimeError("ENCRYPTION_KEY is invalid")


# Runs in a separate, signal-managed subprocess. Migrations use psycopg2.
# The lock is kept on one direct connection while the repo runner opens others.
MIGRATION_CODE = '''
import os, runpy
from sqlalchemy import create_engine, text
engine = create_engine(os.environ["DATABASE_URL"], connect_args={"connect_timeout": 15})
with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
    conn.execute(text("SET statement_timeout = '120s'"))
    conn.execute(text("SELECT pg_advisory_lock(71520261010)"))
    try:
        runpy.run_module("app.run_migrations", run_name="__main__")
    finally:
        conn.execute(text("SELECT pg_advisory_unlock(71520261010)"))
engine.dispose()
'''



def _pid_command(pid):
    """Return the process command line for pid, or None if it is not running."""
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as handle:
            return handle.read().replace(b"\x00", b" ").strip()
    except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
        return None


def _clear_stale_pidfile(path):
    """Remove a leftover Celery pidfile unless a live Celery process owns it.

    A restarted Render instance keeps /tmp. The previous boot's pidfile
    survives, and its pid number usually belongs to an unrelated process in
    the new container, so Celery exits 73 ("already running") and the
    supervisor stops the container in a loop. Only a live process whose
    command line is actually Celery may keep the file; anything else means
    the file is stale. Deleting a file never signals or disrupts the process
    named inside it.
    """
    try:
        with open(path, "r", encoding="ascii", errors="ignore") as handle:
            raw = handle.read().strip().split()[0]
    except (FileNotFoundError, IndexError):
        return
    except OSError:
        log(f"Could not read {path}; leaving it in place")
        return
    try:
        pid = int(raw)
    except ValueError:
        pid = None
    if pid is not None and pid > 0:
        command = _pid_command(pid) or b""
        if b"celery" in command.lower():
            log(f"Active Celery process {pid} found; keeping {path}")
            return
    try:
        os.remove(path)
        log(f"Removed stale pidfile {path}")
    except FileNotFoundError:
        pass
    except OSError:
        log(f"Could not remove stale pidfile {path}; leaving it in place")


def main():
    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    exit_code = 1
    try:
        validate_environment()
        log("Running migrations on direct Neon connection")
        env = os.environ.copy()
        env["DATABASE_URL"] = env["MIGRATION_DATABASE_URL"]
        migration = spawn([sys.executable, "-c", MIGRATION_CODE], env=env)
        deadline = time.monotonic() + 300
        while migration.poll() is None and not stopping:
            if time.monotonic() >= deadline:
                raise RuntimeError("Migrations exceeded 5 minutes; inspect Render logs")
            time.sleep(0.2)
        if stopping:
            return 0
        if migration.returncode:
            raise RuntimeError("Migrations failed; refusing to start API/worker")
        children.remove(migration)
        api = spawn([
            sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0",
            "--port", os.environ.get("PORT", "10000"), "--workers", "1",
            "--timeout-keep-alive", "30", "--proxy-headers",
            "--forwarded-allow-ips", "*",
        ])
        _clear_stale_pidfile("/tmp/miryn-celery.pid")
        worker = spawn([
            sys.executable, "-m", "celery", "-A", "app.workers.celery_app:celery_app",
            "worker", "-B", "--loglevel=info", "--concurrency=1", "--pool=solo",
            "--prefetch-multiplier=1", "--without-gossip", "--without-mingle",
            "--schedule=/tmp/miryn-celerybeat", "--pidfile=/tmp/miryn-celery.pid",
        ])
        log("API and solo Celery worker/beat started")
        while not stopping:
            for name, child in [("API", api), ("Celery worker/beat", worker)]:
                if child.poll() is not None:
                    raise RuntimeError(f"{name} exited ({child.returncode}); stopping container")
            time.sleep(0.5)
        exit_code = 0
    except Exception as exc:
        # Never print connection URLs or keys.
        log(f"Startup/supervision failed: {type(exc).__name__}; inspect child logs")
        if isinstance(exc, RuntimeError):
            log(str(exc))
    finally:
        shutdown()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
