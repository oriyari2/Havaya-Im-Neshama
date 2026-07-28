from unittest import TestCase
from unittest.mock import Mock
from desktop_client.app.presenters.customers_presenter import CustomersPresenter, CustomerProfilePresenter, validate_contact, validate_customer

CUSTOMER={"id":"c1","name":"Task 12B Test Customer","customer_type":"business","city":"Haifa","address":None,"phone":"1","email":"a@b.com","notes":None,"is_active":True,"created_at":"2026-01-01T00:00:00Z","updated_at":"2026-01-01T00:00:00Z","contacts":[]}

class CustomersPresenterTests(TestCase):
    def setUp(self): self.view=Mock(); self.service=Mock(); self.service.list_customers.return_value={"items":[CUSTOMER],"count":1}; self.service.customer.return_value=CUSTOMER; self.presenter=CustomersPresenter(self.view,self.service)
    def test_load_filters_sort_and_pagination(self):
        self.presenter.load(); self.view.show_customers.assert_called_once(); self.presenter.apply_filters({"search":"Task","city":"Haifa","order_by":"created_at"}); self.presenter.page(25,25); self.assertEqual(self.service.list_customers.call_args.args[0]["offset"],25)
    def test_select_and_customer_mutations(self):
        self.presenter.select("c1"); self.view.show_details.assert_called(); self.presenter.begin_edit(); self.view.open_customer_form.assert_called()
        form=Mock(); self.service.update_customer.return_value=CUSTOMER; self.presenter.submit_edit({"name":"Task","email":"ok@example.com"},form); form.close_success.assert_called_once()
        self.view.confirm_customer_deactivation.return_value=True; self.service.deactivate_customer.return_value={**CUSTOMER,"is_active":False}; self.presenter.deactivate(); self.service.deactivate_customer.assert_called_once_with("c1")
    def test_contact_crud_and_duplicate_guard(self):
        self.presenter.select("c1"); form=Mock(); self.presenter.submit_contact_create({"full_name":"Contact"},form); self.service.create_contact.assert_called_once(); form.close_success.assert_called_once()
        contact={"id":"x","full_name":"Contact","is_active":True}; self.view.confirm_contact_deactivation.return_value=True; self.presenter.deactivate_contact(contact); self.service.deactivate_contact.assert_called_once_with("x")
        self.presenter._submitting=True; self.presenter.submit_contact_create({"full_name":"Again"},Mock()); self.assertEqual(self.service.create_contact.call_count,1)
    def test_validation_preserves_form(self):
        form=Mock(); self.presenter.submit_create({"name":"","email":"bad"},form); form.show_error.assert_called(); form.close_success.assert_not_called()
        with self.assertRaises(ValueError): validate_customer({"name":"A","email":"bad"})
        with self.assertRaises(ValueError): validate_contact({"full_name":""})
    def test_profile_is_owned_id_only(self):
        profile=CustomerProfilePresenter(self.view,self.service,"owned"); profile.load(); self.service.customer.assert_called_with("owned"); self.view.show_profile.assert_called()
