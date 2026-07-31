from unittest import TestCase
from unittest.mock import Mock, call
from desktop_client.app.api.client import ApiError, ApiErrorKind
from desktop_client.app.presenters.customers_presenter import CustomersPresenter, CustomerProfilePresenter, validate_customer

CONTACT={"id":"ct1","full_name":"Contact","phone":"050","is_primary":True,"is_active":True}
CUSTOMER={"id":"c1","name":"Task 12B Test Customer","customer_type":"business","city":"Haifa","address":None,"phone":"1","email":"a@b.com","notes":None,"is_active":True,"created_at":"2026-01-01T00:00:00Z","updated_at":"2026-01-01T00:00:00Z","contacts":[CONTACT]}

class CustomersPresenterTests(TestCase):
    def setUp(self): self.view=Mock(); self.service=Mock(); self.service.list_customers.return_value={"items":[CUSTOMER],"count":1}; self.service.customer.return_value=CUSTOMER; self.presenter=CustomersPresenter(self.view,self.service)
    def test_load_filters_sort_and_pagination(self):
        self.presenter.load(); self.view.show_customers.assert_called_once(); self.presenter.apply_filters({"search":"Task","city":"Haifa","order_by":"created_at"}); self.presenter.page(25,25); self.assertEqual(self.service.list_customers.call_args.args[0]["offset"],25)
    def test_reset_clears_presenter_selection_without_sending_ui_metadata_to_service(self):
        self.presenter.select("c1"); self.presenter.apply_filters({"search":None,"order_by":"name","_clear_selection":True})
        self.assertIsNone(self.presenter.selected_id); self.assertNotIn("_clear_selection",self.service.list_customers.call_args.args[0]); self.view.clear_details.assert_called()
    def test_unchanged_reopen_skips_table_rebuild_and_blocking_loading_reset(self):
        self.presenter.load(); self.view.show_customers.reset_mock(); self.view.set_loading.reset_mock(); self.presenter.load(); self.view.show_customers.assert_not_called(); self.assertNotIn(call(True),self.view.set_loading.call_args_list)
    def test_select_and_customer_mutations(self):
        self.presenter.select("c1"); self.view.show_details.assert_called(); self.presenter.begin_edit(); self.view.open_customer_form.assert_called()
        form=Mock(); self.service.update_customer.return_value=CUSTOMER; self.presenter.submit_edit({"name":"Task","email":"ok@example.com","contact_name":"Updated","contact_phone":"051"},form); form.close_success.assert_called_once(); self.assertEqual(self.service.update_customer.call_args.args[1]["contact_name"], "Updated")
        self.view.confirm_customer_deletion.return_value=True; self.presenter.delete(); self.service.delete_customer.assert_called_once_with("c1"); self.view.clear_details.assert_called(); self.assertIsNone(self.presenter.selected_id)
    def test_delete_conflict_preserves_selection_and_duplicate_guard(self):
        self.presenter.select("c1"); self.view.confirm_customer_deletion.return_value=True; self.service.delete_customer.side_effect=ApiError("customer has bookings",status_code=409,kind=ApiErrorKind.CONFLICT)
        self.presenter.delete(); self.assertEqual(self.presenter.selected_id,"c1"); self.view.show_error.assert_called_with("לא ניתן למחוק את הלקוח כל עוד קיימות רשומות תלויות."); self.service.delete_customer.reset_mock(); self.presenter._submitting=True; self.presenter.delete(); self.service.delete_customer.assert_not_called()
    def test_delete_connection_failure_preserves_selection(self):
        self.presenter.select("c1"); self.view.confirm_customer_deletion.return_value=True; self.service.delete_customer.side_effect=ApiError("offline",kind=ApiErrorKind.CONNECTION)
        self.presenter.delete(); self.assertEqual(self.presenter.selected_id,"c1"); self.view.show_error.assert_called()
    def test_delete_cancellation_and_stale_404(self):
        self.presenter.select("c1"); self.view.confirm_customer_deletion.return_value=False; self.presenter.delete(); self.service.delete_customer.assert_not_called()
        self.view.confirm_customer_deletion.return_value=True; self.service.delete_customer.side_effect=ApiError("gone",status_code=404,kind=ApiErrorKind.NOT_FOUND); self.presenter.delete(); self.assertIsNone(self.presenter.selected_id); self.view.clear_details.assert_called()
    def test_create_customer_creates_one_primary_contact(self):
        form=Mock(); self.service.create_customer.return_value={**CUSTOMER,"contacts":[CONTACT]}; self.presenter.submit_create({"name":"New","contact_name":"Contact","contact_phone":"050"},form); payload=self.service.create_customer.call_args.args[0]; self.assertEqual(payload["contact_name"], "Contact"); self.assertEqual(payload["contact_phone"], "050"); form.close_success.assert_called_once()
    def test_validation_preserves_form(self):
        form=Mock(); self.presenter.submit_create({"name":"","email":"bad"},form); form.show_error.assert_called(); form.close_success.assert_not_called()
        with self.assertRaises(ValueError): validate_customer({"name":"A","email":"bad","contact_name":"Contact","contact_phone":"050"})
        with self.assertRaises(ValueError): validate_customer({"name":"A","contact_name":"","contact_phone":"050"})
    def test_profile_is_owned_id_only(self):
        profile=CustomerProfilePresenter(self.view,self.service,"owned"); profile.load(); self.service.customer.assert_called_with("owned"); self.view.show_profile.assert_called()
    def test_stale_detail_does_not_render_or_reset_newer_detail_state(self):
        second={**CUSTOMER,"id":"c2","name":"Second"}; calls=iter([None])
        def nested(customer_id):
            if customer_id=="c1" and next(calls,"done") is None:
                self.presenter.select("c2"); return CUSTOMER
            return second
        self.service.customer.side_effect=nested; self.presenter.select("c1")
        self.assertEqual(self.presenter.selected_id,"c2"); self.assertEqual([call.args[1]["id"] for call in self.view.show_details.call_args_list],["c2"])
        self.assertEqual(self.view.set_detail_loading.call_args_list, [call(True), call(True), call(False)])
    def test_request_identity_generation_resource_and_session_invalidation(self):
        first=self.presenter._begin_request("detail","c1"); second=self.presenter._begin_request("detail","c2"); listing=self.presenter._begin_request("list")
        self.assertLess(first.generation,second.generation); self.assertEqual(second.resource_id,"c2"); self.assertTrue(self.presenter._is_current(second)); self.assertTrue(self.presenter._is_current(listing)); self.assertFalse(self.presenter._is_current(first))
        self.presenter.invalidate_requests(); self.assertFalse(self.presenter._is_current(second)); self.assertFalse(self.presenter._is_current(listing))
    def test_duplicate_and_loading_guards_release_after_failures(self):
        self.service.list_customers.side_effect=ApiError("offline",kind=ApiErrorKind.CONNECTION); self.presenter.load(); self.assertFalse(self.presenter._loading); self.assertEqual(self.view.set_loading.call_args_list[-1],call(False))
        self.service.create_customer.side_effect=ApiError("failed",kind=ApiErrorKind.SERVER); form=Mock(); self.presenter.submit_create({"name":"Customer","contact_name":"Contact","contact_phone":"050"},form); self.assertFalse(self.presenter._submitting); form.set_submitting.assert_called_with(False)
    def test_unexpected_exception_text_is_not_exposed(self):
        self.service.list_customers.side_effect=RuntimeError("database password leaked"); self.presenter.load()
        message=self.view.show_error.call_args.args[0]; self.assertNotIn("password",message); self.assertEqual(message,"לא ניתן להשלים את הפעולה. נסו שוב.")
