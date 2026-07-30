from unittest import TestCase
from unittest.mock import Mock

from desktop_client.app.api.client import ApiError, ApiErrorKind
from desktop_client.app.presenters.users_presenter import UsersPresenter


USER = {"id":"u1","email":"user@example.com","role":"manager","display_name":"Manager","is_active":True,"customer_id":None,"customer_name":None,"instructor_id":None,"instructor_name":None,"created_at":"","updated_at":""}


class UsersPresenterTests(TestCase):
    def setUp(self) -> None:
        self.view=Mock(); self.service=Mock()
        self.service.list_users.return_value={"items":[USER],"count":1}; self.service.user.return_value=USER
        self.presenter=UsersPresenter(self.view,self.service,current_user_id="manager-id",session_role="manager")

    def test_load_search_role_status_page_and_detail(self) -> None:
        self.presenter.load(); self.view.show_users.assert_called_once(); self.presenter.apply_filters({"search":"user","role":"customer","is_active":False}); self.presenter.page(25,25); self.presenter.select("u1")
        filters=self.service.list_users.call_args.args[0]; self.assertEqual((filters["search"],filters["role"],filters["is_active"],filters["offset"]),("user","customer",False,25)); self.view.show_details.assert_called()

    def test_non_manager_presenter_guard(self) -> None:
        presenter=UsersPresenter(self.view,self.service,current_user_id="u",session_role="customer"); presenter.load(); presenter.begin_create()
        self.service.list_users.assert_not_called(); self.view.show_error.assert_called_with("אין הרשאה לניהול משתמשים.",permission=True)

    def test_create_role_profiles_validation_and_duplicate_guard(self) -> None:
        self.presenter.begin_create(); self.view.open_create.assert_called()
        form=Mock(); self.service.create_user.return_value={**USER,"id":"c-user"}
        self.presenter.submit_create({"email":" C@Example.com ","password":"password1","password_confirmation":"password1","role":"customer","customer_name":" Customer ","customer_type":" School ","customer_city":" Haifa ","contact_name":" Contact ","contact_phone":" 050 "},form)
        payload=self.service.create_user.call_args.args[0]; self.assertEqual(payload["email"],"c@example.com"); self.assertEqual((payload["customer_name"],payload["customer_type"],payload["customer_city"],payload["contact_name"],payload["contact_phone"]),("Customer","School","Haifa","Contact","050")); self.assertNotIn("customer_id",payload); form.close_success.assert_called()
        instructor_form=Mock(); self.service.create_user.return_value={**USER,"id":"i-user"}; self.presenter.submit_create({"email":"i@example.com","password":"password1","password_confirmation":"password1","role":"instructor","instructor_name":" Instructor ","instructor_phone":" 051 ","instructor_city":" Jerusalem "},instructor_form)
        instructor=self.service.create_user.call_args.args[0]; self.assertEqual((instructor["email"],instructor["instructor_name"],instructor["instructor_phone"],instructor["instructor_city"]),("i@example.com","Instructor","051","Jerusalem")); self.assertNotIn("instructor_id",instructor)
        manager_form=Mock(); self.service.create_user.return_value={**USER,"id":"m-user"}; self.presenter.submit_create({"email":"m@example.com","password":"password1","password_confirmation":"password1","role":"manager","manager_name":" Manager "},manager_form); manager=self.service.create_user.call_args.args[0]; self.assertEqual(manager,{"email":"m@example.com","password":"password1","role":"manager","manager_name":"Manager"})
        self.presenter.submitting=True; self.presenter.submit_create({"email":"x@example.com"},Mock()); self.assertEqual(self.service.create_user.call_count,3)
        self.presenter.submitting=False; invalid=Mock(); self.presenter.submit_create({"email":"bad","password":"x","password_confirmation":"y","role":"manager"},invalid); invalid.show_error.assert_called()

    def test_email_edit_activate_deactivate_and_reset(self) -> None:
        self.presenter.selected_id="u1"; self.presenter.selected=USER
        form=Mock(); self.service.update_email.return_value={**USER,"email":"new@example.com"}; self.presenter.submit_edit({"email":"NEW@example.com"},form); self.service.update_email.assert_called_with("u1","new@example.com")
        self.service.activate.return_value={**USER,"is_active":True}; self.presenter.activate(); self.service.activate.assert_called_with("u1")
        self.view.confirm_deactivation.return_value=True; self.service.deactivate.return_value={**USER,"is_active":False}; self.presenter.deactivate(); self.service.deactivate.assert_called_with("u1")
        reset=Mock(); self.presenter.selected_id="u1"; self.presenter.selected=USER; self.presenter.submit_reset_password({"password":"newpass123","password_confirmation":"newpass123"},reset); self.service.reset_password.assert_called_with("u1","newpass123")

    def test_error_states_and_guard_release(self) -> None:
        for kind in (ApiErrorKind.VALIDATION,ApiErrorKind.CONFLICT,ApiErrorKind.PERMISSION,ApiErrorKind.CONNECTION,ApiErrorKind.SERVER): self.assertTrue(self.presenter.message(ApiError("raw",kind=kind)))
        self.service.create_user.side_effect=ApiError("duplicate",status_code=409,kind=ApiErrorKind.CONFLICT); form=Mock(); self.presenter.submit_create({"email":"x@example.com","password":"password1","password_confirmation":"password1","role":"manager","manager_name":"Manager"},form); self.assertFalse(self.presenter.submitting); form.show_error.assert_called()
