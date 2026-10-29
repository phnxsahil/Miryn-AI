import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
import importlib
import pytest
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'miryn/backend'))


@pytest.fixture(scope="module", autouse=True)
def mocked_identity_engine_import():
    import sqlalchemy.exc as real_sqlalchemy_exc
    sqlalchemy_mock = MagicMock()
    sqlalchemy_mock.exc = real_sqlalchemy_exc
    sqlalchemy_exc_mock = real_sqlalchemy_exc
    mocked_modules = {
        "app.core.database": MagicMock(),
        "app.services.identity": MagicMock(),
        "sqlalchemy": sqlalchemy_mock,
        "sqlalchemy.exc": sqlalchemy_exc_mock,
        "sqlalchemy.orm": MagicMock(),
    }

    sys.modules.pop("app.services.identity_engine", None)
    with patch.dict(sys.modules, mocked_modules):
        module = importlib.import_module("app.services.identity_engine")
        globals()["IdentityEngine"] = module.IdentityEngine
        yield

    sys.modules.pop("app.services.identity_engine", None)

class TestIdentityEvolutionLog(unittest.TestCase):
    def setUp(self):
        self.engine = IdentityEngine()
        self.session = MagicMock()
        self.user_id = "test-user"
        self.identity_id = "test-identity"
        self.trigger_type = "update_identity"

    def test_log_identity_evolution_sql_bulk(self):
        # Initial state: multiple fields changed
        previous = {
            "state": "old_state",
            "traits": {"a": 1},
            "values": {"v": 1}
        }
        current = {
            "state": "new_state",
            "traits": {"a": 2},
            "values": {"v": 2}
        }

        # After optimization, this should call session.execute 1 time
        self.engine._log_identity_evolution_sql(
            self.session, self.user_id, self.identity_id, previous, current, self.trigger_type
        )

        # Verify the number of calls - should be 1
        print(f"Number of session.execute calls: {self.session.execute.call_count}")
        self.assertEqual(self.session.execute.call_count, 1)

        # Verify the parameters
        args, kwargs = self.session.execute.call_args
        params = args[1]
        self.assertEqual(len(params), 3)
        self.assertEqual(params[0]['f'], 'state')
        self.assertEqual(params[1]['f'], 'traits')
        self.assertEqual(params[2]['f'], 'values')

    def test_log_identity_evolution_sql_no_changes(self):
        # No fields changed
        previous = {"state": "same"}
        current = {"state": "same"}

        self.engine._log_identity_evolution_sql(
            self.session, self.user_id, self.identity_id, previous, current, self.trigger_type
        )

        # Should not call session.execute
        self.assertEqual(self.session.execute.call_count, 0)

    def test_update_identity_serializes_datetime_open_loop(self):
        created_at = datetime.now()
        self.engine.get_identity = MagicMock(return_value={
            "state": "onboarding",
            "traits": {},
            "values": {},
            "beliefs": [],
            "open_loops": [],
            "patterns": [],
            "emotions": [],
            "conflicts": [],
            "memory_weights": {},
        })
        self.session.execute.return_value.mappings.return_value.first.return_value = {
            "id": "row-1",
            "user_id": self.user_id,
            "version": 1,
            "state": "onboarding",
            "traits": "{}",
            "values": "{}",
            "beliefs": "[]",
            "open_loops": "[]",
            "patterns": "[]",
            "emotions": "[]",
            "conflicts": "[]",
            "preset": None,
            "memory_weights": "{}",
        }

        self.engine.update_identity(
            self.user_id,
            {"open_loops": [{"topic": "test", "last_mentioned": created_at}]},
            sql_session=self.session,
        )

        insert_params = next(
            args[1]
            for args, _ in self.session.execute.call_args_list
            if isinstance(args[1], dict) and "open_loops" in args[1]
        )
        self.assertEqual(
            json.loads(insert_params["open_loops"])[0]["last_mentioned"],
            created_at.isoformat(),
        )

if __name__ == "__main__":
    unittest.main()
