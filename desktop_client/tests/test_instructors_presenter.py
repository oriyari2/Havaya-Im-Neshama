from unittest import TestCase
from unittest.mock import Mock
from desktop_client.app.api.client import ApiError,ApiErrorKind
from desktop_client.app.features.instructors.presenter import InstructorProfilePresenter,InstructorsPresenter,validate_instructor
I={"id":"i1","full_name":"Task 12D","phone":"1","email":"x@example.com","city":"C","notes":"N","is_active":True,"created_at":"","updated_at":""}
class InstructorPresenterTests(TestCase):
    def setUp(self):self.v=Mock();self.s=Mock();self.accounts=Mock();self.s.list_instructors.return_value={"items":[I],"count":1};self.s.instructor.return_value=I;self.p=InstructorsPresenter(self.v,self.s,self.accounts)
    def test_load_filter_sort_page_detail(self):self.p.load();self.p.apply_filters({"search":"Task","city":"C","is_active":True,"order_by":"created_at"});self.p.page(25,25);self.assertEqual(self.s.list_instructors.call_args.args[0]["offset"],25);self.p.select("i1");self.v.show_details.assert_called()
    def test_create_edit_guard_and_validation(self):
        f=Mock();self.accounts.create_user.return_value={"id":"u1","instructor_id":"i1"};self.p.submit_create({"full_name":"Task","email":"x@example.com","password":"password1","password_confirmation":"password1"},f);f.close_success.assert_called();payload=self.accounts.create_user.call_args.args[0];self.assertEqual(payload["role"],"instructor");self.s.create_instructor.assert_not_called();self.p.submitting=True;self.p.submit_create({"full_name":"Again"},Mock());self.assertEqual(self.accounts.create_user.call_count,1)
        with self.assertRaises(ValueError):validate_instructor({"full_name":"","email":"bad"})
    def test_stale_selection_is_cleared(self):
        self.s.instructor.side_effect=ApiError("gone",status_code=404,kind=ApiErrorKind.NOT_FOUND);self.p.select("missing");self.v.clear_details.assert_called()
    def test_lifecycle_uses_logical_deactivate_and_reactivate(self):
        self.p.select("i1");self.v.confirm_deactivation.return_value=True;self.s.deactivate.return_value={**I,"is_active":False};self.p.deactivate();self.s.deactivate.assert_called_once_with("i1")
        self.p.selected={**I,"is_active":False};self.p.selected_id="i1";self.s.activate.return_value=I;self.p.activate();self.s.activate.assert_called_once_with("i1")
    def test_change_password_uses_selected_instructor_account(self):
        self.p.select("i1");self.p.begin_change_password();self.v.open_change_password.assert_called_once();f=Mock();self.p.submit_change_password({"password":"newpass123","password_confirmation":"newpass123"},f);self.s.reset_password.assert_called_once_with("i1","newpass123");f.close_success.assert_called_once()
    def test_profile_uses_me_only(self):
        self.s.my_profile.return_value=I;p=InstructorProfilePresenter(self.v,self.s);p.load();self.s.my_profile.assert_called_once();self.v.show_profile.assert_called()
