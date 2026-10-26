#!/usr/bin/env python3
"""Offline by default. Explicit live opt-in tests LLMService, not user accounts."""
import argparse
import asyncio
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Opt in to real Gemini API use (may cost money/quota).')
    parser.add_argument('--case', action='append', default=[], help='Fixture ID; repeat to select. Live runs require selection.')
    parser.add_argument('--max-cases', type=int, default=1, help='Live case cap, 1-7; default 1.')
    parser.add_argument('--transport', choices=['chat', 'stream'], default='stream')
    parser.add_argument('--output', type=Path, help='Write fictional replies and review rubrics as JSON. No secrets.')
    args = parser.parse_args()
    if not args.live:
        # No app server, credentials, accounts, Redis or production DB required.
        with tempfile.TemporaryDirectory(prefix='miryn-eval-') as directory:
            env = os.environ.copy()
            env.update(SECRET_KEY='offline-eval-not-a-secret',
                       DATABASE_URL=f'sqlite:///{directory}/test.db',
                       SUPABASE_URL='', SUPABASE_SERVICE_ROLE_KEY='', SUPABASE_ANON_KEY='',
                       REDIS_URL='redis://127.0.0.1:1')
            result = subprocess.run([sys.executable, '-m', 'pytest',
                                     'tests/test_safety.py', 'tests/test_llm_stream_fallback.py',
                                     'tests/test_llm_quota.py', '-q'], cwd=ROOT, env=env)
            return result.returncode
    if not 1 <= args.max_cases <= 7:
        parser.error('--max-cases must be between 1 and 7')
    if not args.case:
        parser.error('live mode requires at least one --case; never runs the full suite implicitly')
    if not os.environ.get('GEMINI_API_KEY'):
        parser.error('live mode requires GEMINI_API_KEY in the server environment; never paste it into a prompt or command argument')
    cases = json.loads((ROOT / 'evals/safety_cases.json').read_text())
    ids = {case['id'] for case in cases}
    if set(args.case) - ids:
        parser.error('unknown case ID')
    selected = [case for case in cases if case['id'] in args.case]
    if len(selected) > args.max_cases:
        parser.error('selected cases exceed --max-cases')
    # No imports of API/orchestrator/memory/identity/DB code. Identity is a fresh
    # in-memory dict per case, never loaded from any account.
    # Existing provider code logs raw exception strings. Suppress those in this
    # standalone runner; report only safe error types below.
    logging.disable(logging.CRITICAL)
    os.environ['LLM_PROVIDER'] = 'gemini'
    os.environ.setdefault('SECRET_KEY', 'isolated-evaluation-not-a-secret')
    sys.path.insert(0, str(ROOT))
    from app.services.llm_service import LLMService
    from app.services.safety import immediate_safety_reply

    async def run():
        service = LLMService()
        # Evaluation is pinned to one configured model: no quota-burning chain.
        service.gemini_fallback_models = service.gemini_fallback_models[:1]
        results = []
        for case in selected:
            identity = {'preset': case['preset'], 'timezone': 'UTC'}
            try:
                if args.transport == 'chat':
                    reply = await service.chat({}, case['message'], identity)
                else:
                    reply = ''.join([part async for part in service.stream_chat({}, case['message'], identity)])
                results.append({**case, 'reply': reply,
                                'route_observed': 'local_urgent' if immediate_safety_reply(case['message']) else 'model',
                                'review_status': 'HUMAN_REVIEW_REQUIRED'})
            except Exception as exc:
                # Exception strings can contain provider request details. Do not
                # serialize raw errors or secrets into eval artifacts.
                results.append({'id': case['id'], 'error_type': type(exc).__name__,
                                'review_status': 'ERROR_NOT_A_PASS'})
                break
        return {'mode': 'live', 'transport': args.transport, 'model': service.model,
                'personal_memory_used': False, 'results': results}
    report = asyncio.run(run())
    text = json.dumps(report, indent=2)
    if args.output:
        # Do not accidentally overwrite an earlier evaluation.
        with args.output.open('x') as out:
            out.write(text + '\n')
    else:
        print(text)
    return 1 if any('error_type' in item for item in report['results']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
