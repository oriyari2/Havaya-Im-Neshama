from unittest import TestCase
from unittest.mock import Mock
from desktop_client.app.api.client import ApiError, ApiErrorKind
from desktop_client.app.presenters.activities_presenter import ActivitiesPresenter, validate_activity

ITEM={"id":"a1","name":"Task 12C Test Activity","description":"Created","target_audience":"Task12C Audience","duration_minutes":60,"recommended_capacity":30,"pricing_rule":"fixed","required_equipment":"none","preparation_notes":"prepare","season":"Task12C Season","tags":"task12c","is_active":True,"created_at":"2026-01-01T00:00:00Z","updated_at":"2026-01-01T00:00:00Z"}

class ActivitiesPresenterTests(TestCase):
    def build(self,role="manager"):
        view=Mock(); service=Mock(); service.list_activities.return_value={"items":[ITEM],"count":1}; service.activity.return_value=ITEM; return view,service,ActivitiesPresenter(view,service,role)
    def test_role_initial_queries(self):
        for role,active in (("manager",None),("instructor",True),("customer",True)):
            view,service,p=self.build(role); p.load(); self.assertIs(service.list_activities.call_args.args[0]["is_active"],active); view.set_manager_actions.assert_called_with(role=="manager")
    def test_filters_paging_and_reset(self):
        _,service,p=self.build(); p.apply_filters({"search":"Task","target_audience":"Audience","season":"Season","tag":"tag","is_active":False}); self.assertEqual(service.list_activities.call_args.args[0]["offset"],0); p.page(25,10); query=service.list_activities.call_args.args[0]; self.assertEqual((query["offset"],query["limit"],query["tag"]),(25,10,"tag"))
    def test_non_manager_cannot_override_active_or_mutate(self):
        view,service,p=self.build("customer"); p.apply_filters({"is_active":False}); self.assertIs(service.list_activities.call_args.args[0]["is_active"],True); p.begin_create(); p.deactivate(); service.create_activity.assert_not_called(); view.open_activity_form.assert_not_called()
    def test_detail_create_edit_and_duplicate_guard(self):
        view,service,p=self.build(); p.select("a1"); view.show_details.assert_called(); form=Mock(); service.create_activity.return_value=ITEM; p.submit_create({"name":" A ","duration_minutes":"60","recommended_capacity":"30"},form); service.create_activity.assert_called(); form.close_success.assert_called(); p._submitting=True; p.submit_create({"name":"Again"},Mock()); self.assertEqual(service.create_activity.call_count,1)
    def test_deactivate_reactivate_and_confirmation(self):
        view,service,p=self.build(); p.select("a1"); view.confirm_deactivation.return_value=True; service.deactivate_activity.return_value={**ITEM,"is_active":False}; p.deactivate(); service.deactivate_activity.assert_called_with("a1"); p.selected_activity={**ITEM,"is_active":False}; service.reactivate_activity.return_value=ITEM; p.reactivate(); service.reactivate_activity.assert_called_with("a1")
    def test_validation_failure_preserves_form_and_retry(self):
        _,service,p=self.build(); form=Mock(); p.submit_create({"name":"","duration_minutes":"x"},form); form.show_error.assert_called(); form.close_success.assert_not_called(); p.retry(); self.assertTrue(service.list_activities.called)
        with self.assertRaises(ValueError): validate_activity({"name":"A","recommended_capacity":"0"})
    def test_stale_detail_clears_and_refreshes(self):
        view,service,p=self.build(); service.activity.side_effect=ApiError("gone",status_code=404,kind=ApiErrorKind.NOT_FOUND); p.select("missing"); view.clear_details.assert_called(); self.assertTrue(service.list_activities.called)
