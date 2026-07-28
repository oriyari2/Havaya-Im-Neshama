from unittest import TestCase
from unittest.mock import MagicMock, patch
from uuid import uuid4

from backend.app.application.services import customer_service
from backend.app.core.auth import require_roles
from backend.app.routers import customers, instructors


class CustomerDeletionTests(TestCase):
    @patch.object(customer_service, "get_connection")
    def test_delete_is_physical_and_contacts_cascade_in_same_transaction(self, get_connection):
        customer_id = uuid4()
        conn, cur = MagicMock(), MagicMock()
        get_connection.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = cur
        cur.fetchone.side_effect = [
            {"id": customer_id},
            {"has_user": False, "has_booking": False, "has_event_history": False},
            {"id": customer_id},
        ]

        customer_service.delete_customer(customer_id)

        sql = " ".join(call.args[0] for call in cur.execute.call_args_list)
        self.assertIn("FOR UPDATE", sql)
        self.assertIn("booking_events", sql)
        self.assertIn("DELETE FROM customers", sql)
        self.assertNotIn("UPDATE customers", sql)
        self.assertNotIn("DELETE FROM customer_contacts", sql)
        conn.commit.assert_called_once()

    @patch.object(customer_service, "get_connection")
    def test_each_protected_dependency_blocks_and_rolls_back(self, get_connection):
        for dependency in ("has_user", "has_booking", "has_event_history"):
            with self.subTest(dependency=dependency):
                customer_id = uuid4()
                conn, cur = MagicMock(), MagicMock()
                get_connection.return_value.__enter__.return_value = conn
                conn.cursor.return_value.__enter__.return_value = cur
                flags = {"has_user": False, "has_booking": False, "has_event_history": False}
                flags[dependency] = True
                cur.fetchone.side_effect = [{"id": customer_id}, flags]
                with self.assertRaises(customer_service.CustomerDeleteConflictError):
                    customer_service.delete_customer(customer_id)
                sql = " ".join(call.args[0] for call in cur.execute.call_args_list)
                self.assertNotIn("DELETE FROM customers", sql)
                conn.rollback.assert_called_once()
                conn.commit.assert_not_called()

    @patch.object(customer_service, "get_connection")
    def test_missing_customer_rolls_back_and_reports_not_found(self, get_connection):
        conn, cur = MagicMock(), MagicMock()
        get_connection.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = cur
        cur.fetchone.return_value = None
        with self.assertRaises(customer_service.CustomerNotFoundError):
            customer_service.delete_customer(uuid4())
        conn.rollback.assert_called_once()


class DeletionAuthorizationTests(TestCase):
    def test_customer_and_instructor_delete_reject_non_managers(self):
        dependency = require_roles("manager")
        for role in ("customer", "instructor"):
            with self.subTest(role=role):
                with self.assertRaises(Exception) as raised:
                    dependency({"id": uuid4(), "role": role})
                self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(dependency({"id": uuid4(), "role": "manager"})["role"], "manager")

    @patch.object(customer_service, "delete_customer", side_effect=RuntimeError("foreign key sql detail"))
    def test_customer_router_does_not_expose_raw_database_errors(self, _delete):
        with self.assertRaises(Exception) as raised:
            customers.delete_customer(uuid4(), {"role": "manager"})
        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(raised.exception.detail, "Could not delete customer")

    @patch.object(instructors.service, "delete_instructor", side_effect=RuntimeError("foreign key sql detail"))
    def test_instructor_router_does_not_expose_raw_database_errors(self, _delete):
        with self.assertRaises(Exception) as raised:
            instructors.delete(uuid4(), {"role": "manager"})
        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(raised.exception.detail, "Could not delete instructor")
