from unittest import TestCase
from unittest.mock import Mock
from desktop_client.app.services.customer_service import CustomerService

class CustomerServiceTests(TestCase):
    def setUp(self): self.api = Mock(); self.service = CustomerService(self.api)
    def test_customer_endpoints(self):
        self.service.list_customers({"limit": 25}); self.api.get.assert_called_with("/customers", {"limit": 25})
        self.service.customer("c1"); self.api.get.assert_called_with("/customers/c1")
        self.service.create_customer({"name":"A"}); self.api.post.assert_called_with("/customers", {"name":"A"})
        self.service.update_customer("c1", {"name":"B"}); self.api.put.assert_called_with("/customers/c1", {"name":"B"})
        self.service.deactivate_customer("c1"); self.api.delete.assert_called_with("/customers/c1")
        self.service.reactivate_customer("c1"); self.api.put.assert_called_with("/customers/c1", {"is_active": True})
    def test_contact_endpoints(self):
        self.service.contacts("c1", is_active=False); self.api.get.assert_called_with("/customers/c1/contacts", {"is_active": False})
        self.service.create_contact("c1", {"full_name":"A"}); self.api.post.assert_called_with("/customers/c1/contacts", {"full_name":"A"})
        self.service.update_contact("x", {"full_name":"B"}); self.api.put.assert_called_with("/customer-contacts/x", {"full_name":"B"})
        self.service.deactivate_contact("x"); self.api.delete.assert_called_with("/customer-contacts/x")
        self.service.reactivate_contact("x"); self.api.put.assert_called_with("/customer-contacts/x", {"is_active": True})
