"""Run standalone: python -m unittest discover -s tests -p test_owner_metrics_unit.py"""
import unittest
from datetime import datetime
from contextlib import contextmanager
from unittest.mock import patch
from sqlalchemy import create_engine, text
from app.services.owner_metrics import read_account_metrics

class AccountMetricsTests(unittest.TestCase):
    def test_counts_daily_gaps_soft_deletes_and_no_pii(self):
        engine = create_engine("sqlite://")
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE users(id TEXT, email TEXT, created_at TIMESTAMP, is_deleted BOOLEAN)"))
            for ident, date, deleted in [(1, '2026-10-01 10:00:00', False), (2, '2026-10-30 09:00:00', False), (3, '2026-10-30 18:30:00', True)]:
                conn.execute(text("INSERT INTO users VALUES (:id, 'private@example.test', :date, :deleted)"), {"id":str(ident), "date":date, "deleted":deleted})
            result = read_account_metrics(conn, 3, datetime(2026, 10, 31, 2))
        self.assertEqual(result['accounts_created'], 3)
        self.assertEqual(result['active_accounts'], 2)
        self.assertEqual(result['deleted_accounts'], 1)
        self.assertEqual(result['new_today'], 1)
        self.assertEqual(result['new_last_7_days'], 2)
        self.assertEqual(result['new_in_period'], 2)
        self.assertEqual([row['count'] for row in result['daily_signups']], [0, 1, 1])
        self.assertNotIn('private@example.test', str(result))

    def test_kolkata_midnight_boundary(self):
        engine = create_engine("sqlite://")
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE users(id TEXT, created_at TIMESTAMP, is_deleted BOOLEAN)"))
            for index, moment in enumerate(['2026-10-30 18:29:59', '2026-10-30 18:30:00']):
                conn.execute(text("INSERT INTO users VALUES (:id,:moment,false)"), {"id":str(index), "moment":moment})
            result = read_account_metrics(conn, 2, datetime(2026,10,30,20))
        self.assertEqual(result['new_today'], 1)
        self.assertEqual(result['timezone'], 'Asia/Kolkata')
        self.assertEqual(result['daily_signups'], [{'date':'2026-10-30','count':1},{'date':'2026-10-31','count':1}])

    def test_empty_database_returns_zero(self):
        engine = create_engine("sqlite://")
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE users(id TEXT, created_at TIMESTAMP, is_deleted BOOLEAN)"))
            result = read_account_metrics(conn, 1, datetime(2026, 10, 31))
        self.assertEqual(result['accounts_created'], 0)
        self.assertEqual(result['daily_signups'][0]['count'], 0)

    def test_http_access_and_cache_headers(self):
        import importlib.util
        import sys
        import types
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.config import settings
        from app.core.security import create_access_token
        spec = importlib.util.spec_from_file_location("analytics_http_test", "app/api/analytics.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        app = FastAPI()
        app.include_router(module.router)
        fake_db = types.ModuleType('app.core.database')
        fake_db.has_sql = lambda: True
        @contextmanager
        def session(): yield None
        fake_db.get_sql_session = session
        client = TestClient(app)
        with patch.object(settings, 'ANALYTICS_OWNER_USER_IDS', 'owner-id'):
            self.assertEqual(client.get('/analytics/owner').status_code, 401)
            other = create_access_token('other-id')
            self.assertEqual(client.get('/analytics/owner', headers={'Authorization':'Bearer '+other}).status_code, 403)
            owner = create_access_token('owner-id')
            with patch.dict(sys.modules, {'app.core.database': fake_db}), patch('app.services.owner_metrics.read_account_metrics', return_value={'accounts_created':8}):
                response = client.get('/analytics/owner', headers={'Authorization':'Bearer '+owner})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['cache-control'], 'no-store, private')
            self.assertEqual(response.json(), {'accounts_created':8})

    def test_owner_authorization_fails_closed(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("analytics_under_test", "app/api/analytics.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        require_analytics_owner = module.require_analytics_owner
        from app.config import settings
        from fastapi import HTTPException
        with patch.object(settings, 'ANALYTICS_OWNER_USER_IDS', ''):
            with self.assertRaises(HTTPException) as exc: require_analytics_owner('someone')
            self.assertEqual(exc.exception.status_code, 403)
        with patch.object(settings, 'ANALYTICS_OWNER_USER_IDS', ' owner-id , another-id '):
            self.assertEqual(require_analytics_owner('owner-id'), 'owner-id')
            with self.assertRaises(HTTPException): require_analytics_owner('not-owner')

if __name__ == '__main__': unittest.main()
