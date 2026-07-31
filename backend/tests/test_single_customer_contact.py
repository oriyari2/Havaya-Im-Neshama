from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from backend.app.application.services import customer_service
from backend.app.routers import customers as customer_router
from backend.app.schemas.customer import CustomerContactCreate, CustomerContactUpdate, CustomerCreate, CustomerUpdate


class SingleCustomerContactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = MagicMock()
        self.cursor = MagicMock()
        self.connection.__enter__.return_value = self.connection
        self.connection.cursor.return_value.__enter__.return_value = self.cursor
        self.connection.cursor.return_value.__exit__.return_value = False
        self.connection.__exit__.return_value = False
        self.connection_patch = patch(
            "backend.app.application.services.customer_service.get_connection",
            return_value=self.connection,
        )
        self.connection_patch.start()

    def tearDown(self) -> None:
        self.connection_patch.stop()

    def test_customer_read_exposes_only_primary_current_contact(self) -> None:
        customer_id = uuid4()
        primary = {"id": uuid4(), "customer_id": customer_id, "is_primary": True, "is_active": True}
        secondary = {"id": uuid4(), "customer_id": customer_id, "is_primary": False, "is_active": True}
        with patch.object(customer_service.repo, "get_customer", return_value={"id": customer_id}), patch.object(
            customer_service.repo, "list_contacts", return_value=[secondary, primary]
        ):
            _customer, contacts = customer_service.get_customer_for_user(
                customer_id, {"role": "manager"}
            )
        self.assertEqual(contacts, [primary])

    def test_second_active_contact_is_rejected_without_write(self) -> None:
        customer_id = uuid4()
        existing = {"id": uuid4(), "customer_id": customer_id, "is_primary": True, "is_active": True}
        payload = CustomerContactCreate(full_name="Second", phone="050", is_primary=True)
        with patch.object(customer_service.repo, "get_customer", return_value={"id": customer_id}), patch.object(
            customer_service.repo, "list_contacts", return_value=[existing]
        ), patch.object(customer_service.repo, "create_contact") as create:
            with self.assertRaises(customer_service.ContactConflictError):
                customer_service.create_customer_contact(customer_id, payload)
        create.assert_not_called()
        self.connection.commit.assert_not_called()

    def test_inactive_historical_contact_cannot_be_reactivated_beside_current(self) -> None:
        customer_id, contact_id = uuid4(), uuid4()
        existing = {"id": contact_id, "customer_id": customer_id, "is_primary": False, "is_active": False}
        current = {"id": uuid4(), "customer_id": customer_id, "is_primary": True, "is_active": True}
        with patch.object(customer_service.repo, "get_contact", return_value=existing), patch.object(
            customer_service.repo, "list_contacts", return_value=[current]
        ), patch.object(customer_service.repo, "update_contact") as update:
            with self.assertRaises(customer_service.ContactConflictError):
                customer_service.update_customer_contact(contact_id, CustomerContactUpdate(is_active=True))
        update.assert_not_called()

    def test_router_maps_second_active_contact_to_conflict(self) -> None:
        customer_id = uuid4()
        payload = CustomerContactCreate(full_name="Second", phone="050", is_primary=True)
        with patch.object(
            customer_service,
            "create_customer_contact",
            side_effect=customer_service.ContactConflictError("already exists"),
        ):
            with self.assertRaisesRegex(Exception, "409") as raised:
                customer_router.create_customer_contact(
                    customer_id, payload, {"role": "manager"}
                )
        self.assertEqual(getattr(raised.exception, "status_code", None), 409)

    def test_customer_and_contact_are_created_in_one_transaction(self) -> None:
        customer_id = uuid4()
        payload = CustomerCreate(name="School", contact_name="Contact", contact_phone="050")
        with patch.object(customer_service.repo, "create_customer", return_value={"id": customer_id}) as create_customer, patch.object(
            customer_service.repo, "create_contact", return_value={"id": uuid4()}
        ) as create_contact:
            customer, contacts = customer_service.create_customer(payload)
        self.assertEqual(customer["id"], customer_id)
        self.assertEqual(len(contacts), 1)
        self.assertNotIn("contact_name", create_customer.call_args.args[1])
        self.assertEqual(create_contact.call_args.args[2]["full_name"], "Contact")
        self.assertEqual(create_contact.call_args.args[2]["phone"], "050")
        self.connection.commit.assert_called_once()

    def test_contact_failure_does_not_commit_customer(self) -> None:
        payload = CustomerCreate(name="School", contact_name="Contact", contact_phone="050")
        with patch.object(customer_service.repo, "create_customer", return_value={"id": uuid4()}), patch.object(
            customer_service.repo, "create_contact", side_effect=RuntimeError("write failed")
        ):
            with self.assertRaises(RuntimeError):
                customer_service.create_customer(payload)
        self.connection.commit.assert_not_called()

    def test_contact_update_fields_must_be_supplied_together(self) -> None:
        with self.assertRaises(ValueError):
            CustomerUpdate(contact_name="Only name")


if __name__ == "__main__":
    unittest.main()
