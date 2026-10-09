import unittest
from unittest.mock import MagicMock, patch
import importlib
import pytest
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'miryn/backend'))


@pytest.fixture(scope="module", autouse=True)
def mocked_identity_engine_import():
    sqlalchemy_mock = MagicMock()
    sqlalchemy_exc_mock = MagicMock()
    sqlalchemy_mock.exc = sqlalchemy_exc_mock
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

if __name__ == "__main__":
    unittest.main()
