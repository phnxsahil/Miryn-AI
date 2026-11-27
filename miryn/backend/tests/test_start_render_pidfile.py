"""Startup pidfile handling in start-render.py.

A restarted Render instance keeps /tmp, so yesterday's Celery pidfile can
make today's worker exit 73 in a crash loop. These tests cover the stale /
live / absent / malformed cases without Docker, Redis or a database.
"""

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "start-render.py"
spec = importlib.util.spec_from_file_location("start_render", MODULE_PATH)
start_render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(start_render)


def _spawn(cmdline_first_word):
    """Spawn a live process whose /proc cmdline starts with the given word."""
    proc = subprocess.Popen(
        ["bash", "-c", f'exec -a {cmdline_first_word} sleep 30'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.1)
    return proc


@pytest.fixture
def pidfile(tmp_path):
    return tmp_path / "miryn-celery.pid"


def test_absent_file_is_noop(pidfile):
    start_render._clear_stale_pidfile(str(pidfile))
    assert not pidfile.exists()


def test_malformed_content_removed(pidfile):
    pidfile.write_text("not-a-pid")
    start_render._clear_stale_pidfile(str(pidfile))
    assert not pidfile.exists()


def test_dead_pid_removed(pidfile):
    dead = subprocess.Popen(["true"])
    dead.wait()
    pidfile.write_text(str(dead.pid))
    start_render._clear_stale_pidfile(str(pidfile))
    assert not pidfile.exists()


def test_live_unrelated_process_removed(pidfile):
    proc = _spawn("uvicorn")
    try:
        pidfile.write_text(str(proc.pid))
        start_render._clear_stale_pidfile(str(pidfile))
        assert not pidfile.exists()
        assert proc.poll() is None  # file removal never touches the process
    finally:
        proc.kill()
        proc.wait()


def test_live_celery_process_kept(pidfile):
    proc = _spawn("celery-worker")
    try:
        pidfile.write_text(str(proc.pid))
        start_render._clear_stale_pidfile(str(pidfile))
        assert pidfile.exists()
        assert proc.poll() is None
    finally:
        proc.kill()
        proc.wait()
