from unittest import TestCase
from unittest.mock import Mock
from desktop_client.app.api.client import ApiError,ApiErrorKind
from desktop_client.app.presenters.booking_assignments_presenter import BookingAssignmentsPresenter
A={"booking_activity_id":"ba","activity_id":"a","activity_name":"Activity","assignment_required":True,"assignments":[]};M={"booking_id":"b","version":2,"activities":[A]};I={"id":"i","full_name":"Instructor","city":"C"}
class AssignmentPresenterTests(TestCase):
    def setUp(self):self.v=Mock();self.s=Mock();self.ins=Mock();self.s.assignments.return_value=M;self.refresh=Mock();self.related=Mock();self.confirm=Mock();self.p=BookingAssignmentsPresenter(self.v,self.s,self.ins,refresh_booking=self.refresh,refresh_related=self.related,confirm_after_assignment=self.confirm)
    def test_load_and_switch(self):self.p.select_booking("b");self.s.assignments.assert_called_with("b");self.v.show_assignments.assert_called_with([A]);self.p.select_booking("b2");self.assertEqual(self.p.booking_id,"b2")
    def test_assign_remove_version_refresh_and_guard(self):
        self.p.select_booking("b");self.s.assign.return_value={"id":"b","version":3};self.p.assign(A,I);self.s.assign.assert_called_with("b","ba","i",2);self.refresh.assert_called_with("b");self.related.assert_called();assignment={"instructor_id":"i","instructor_name":"Instructor"};self.v.confirm_assignment_removal.return_value=True;self.s.remove.return_value={"id":"b","version":4};self.p.remove(A,assignment);self.s.remove.assert_called();self.p.submitting=True;self.p.assign(A,I);self.assertEqual(self.s.assign.call_count,1)
    def test_conflict_refreshes_without_retry(self):
        self.p.select_booking("b");self.s.assign.side_effect=ApiError("conflict",status_code=409,kind=ApiErrorKind.CONFLICT);self.p.assign(A,I);self.assertGreaterEqual(self.s.assignments.call_count,2);self.v.show_assignments_error.assert_called()
    def test_assignment_after_creation_reuses_existing_assign_command(self):
        self.s.assign.return_value={"id":"new","version":2};self.p.assign_after_creation({"id":"new"},"i");self.s.assignments.assert_called_with("new");self.s.assign.assert_called_with("new","ba","i",2)
    def test_pending_combined_action_assigns_then_confirms_with_new_version(self):
        self.p.select_booking("b");self.s.assign.return_value={"id":"b","version":3,"status":"NEW"};self.v.open_instructor_selector.side_effect=lambda activity,query,choose: Mock(activity=activity);self.p.begin_assign_and_confirm(A);choose=self.v.open_instructor_selector.call_args.args[2];choose(I);self.confirm.assert_called_once_with({"id":"b","version":3,"status":"NEW"})
    def test_pending_already_assigned_confirms_without_duplicate_assignment(self):
        assigned_activity={**A,"assignments":[{"instructor_id":"i"}]};self.p.model={"booking_id":"b","version":3,"activities":[assigned_activity]};self.p.booking_id="b";self.p.begin_assign_and_confirm(assigned_activity);self.confirm.assert_called_once_with({"id":"b","version":3,"status":"NEW"});self.v.open_instructor_selector.assert_not_called();self.s.assign.assert_not_called()
