from unittest import TestCase
from unittest.mock import Mock
from desktop_client.app.features.customers.service import CustomerService

class CustomerServiceTests(TestCase):
    def setUp(self): self.api = Mock(); self.service = CustomerService(self.api)
    def test_customer_endpoints(self):
        self.service.list_customers({"limit": 25}); self.api.get.assert_called_with("/customers", {"limit": 25})
        self.service.customer("c1"); self.api.get.assert_called_with("/customers/c1")
        self.service.create_customer({"name":"A"}); self.api.post.assert_called_with("/customers", {"name":"A"})
        self.service.update_customer("c1", {"name":"B"}); self.api.put.assert_called_with("/customers/c1", {"name":"B"})
        self.service.deactivate("c1"); self.api.post.assert_called_with("/customers/c1/deactivate", {})
        self.service.activate("c1"); self.api.post.assert_called_with("/customers/c1/activate", {})
        self.assertFalse(hasattr(self.service, "delete_customer"))
        self.service.reset_password("c1","newpass123"); self.api.post.assert_called_with("/customers/c1/reset-password",{"new_password":"newpass123"})
    def test_obsolete_contact_endpoints_are_not_exposed(self):
        self.assertFalse(hasattr(self.service, "create_contact"))
        self.assertFalse(hasattr(self.service, "update_contact"))
        self.assertFalse(hasattr(self.service, "contacts"))
        self.assertFalse(hasattr(self.service, "deactivate_contact"))
        self.assertFalse(hasattr(self.service, "reactivate_contact"))
