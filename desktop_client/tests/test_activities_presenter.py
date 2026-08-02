from unittest import TestCase
from unittest.mock import Mock
from desktop_client.app.api.client import ApiError, ApiErrorKind
from desktop_client.app.presenters.activities_presenter import ActivitiesPresenter, validate_activity
from desktop_client.app.media_config import MAX_PREVIEW_CACHE_ENTRIES

ITEM={"id":"a1","name":"Task 12C Test Activity","description":"Created","target_audience":"Task12C Audience","duration_minutes":60,"recommended_capacity":30,"pricing_rule":"fixed","required_equipment":"none","preparation_notes":"prepare","season":"Task12C Season","tags":"task12c","is_active":True,"created_at":"2026-01-01T00:00:00Z","updated_at":"2026-01-01T00:00:00Z"}
IMAGES=[{"id":"i1","activity_id":"a1","secure_url":"https://cdn.example/i1","original_filename":"one.png","is_primary":True},{"id":"i2","activity_id":"a1","secure_url":"https://cdn.example/i2","original_filename":"two.png","is_primary":False}]

class ActivitiesPresenterTests(TestCase):
    def build(self,role="manager"):
        view=Mock(); service=Mock(); service.list_activities.return_value={"items":[ITEM],"count":1}; service.activity.return_value=ITEM; return view,service,ActivitiesPresenter(view,service,role)
    def test_role_initial_queries(self):
        for role,active in (("manager",None),("instructor",True),("customer",True)):
            view,service,p=self.build(role); p.load(); self.assertIs(service.list_activities.call_args.args[0]["is_active"],active); view.set_manager_actions.assert_called_with(role=="manager")
    def test_filters_paging_and_reset(self):
        _,service,p=self.build(); p.apply_filters({"search":"Task","target_audience":"Audience","season":"Season","tag":"tag","is_active":False}); self.assertEqual(service.list_activities.call_args.args[0]["offset"],0); p.page(25,10); query=service.list_activities.call_args.args[0]; self.assertEqual((query["offset"],query["limit"],query["tag"]),(25,10,"tag"))
    def test_repeated_navigation_resets_activity_state(self):
        view,service,p=self.build();p.selected_id="a1";p.selected_activity=ITEM;p.reset_to_default();self.assertIsNone(p.selected_id);self.assertIsNone(p.selected_activity);view.reset_to_default.assert_called_once()
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
    def test_primary_preview_and_role_safe_media_actions(self):
        view,service,p=self.build(); service.activity.return_value={**ITEM,"images":IMAGES}; service.preview_bytes.return_value=b"image"; view.show_preview.return_value=True; p.select("a1")
        service.preview_bytes.assert_called_with("https://cdn.example/i1"); view.select_image.assert_called_with("i1")
        customer_view,customer_service,customer=self.build("customer"); customer.upload_image("x.png"); customer.delete_image(); customer_service.upload_image.assert_not_called(); customer_service.delete_image.assert_not_called(); customer_view.set_media_actions.assert_called_with(False)
    def test_upload_delete_refresh_and_confirmation(self):
        view,service,p=self.build(); service.activity.return_value={**ITEM,"images":IMAGES}; service.preview_bytes.return_value=b"image"; view.show_preview.return_value=True; p.select("a1")
        p.upload_image("one.png"); service.upload_image.assert_called_with("a1","one.png")
        p.select("a1"); view.confirm_image_deletion.return_value=False; p.delete_image(); service.delete_image.assert_not_called()
        view.confirm_image_deletion.return_value=True; p.delete_image(); service.delete_image.assert_called_with("a1","i1")
    def test_preview_cache_is_bounded_and_cleared(self):
        view,service,p=self.build(); view.show_preview.return_value=True; service.preview_bytes.side_effect=lambda url:url.encode()
        for index in range(MAX_PREVIEW_CACHE_ENTRIES+1):
            image={"id":f"i{index}","secure_url":f"https://cdn.example/i{index}"}; p.selected_id="a1"; p.selected_image_id=f"i{index}"; p._load_preview(image)
        self.assertEqual(len(p._preview_cache),MAX_PREVIEW_CACHE_ENTRIES); self.assertNotIn(("a1","i0","https://cdn.example/i0"),p._preview_cache)
        p.clear_preview_cache(); self.assertEqual(len(p._preview_cache),0)
    def test_cache_hit_avoids_download_and_lru_access_promotes(self):
        view,service,p=self.build(); view.show_preview.return_value=True; service.preview_bytes.side_effect=lambda url:url.encode(); p.selected_id="a1"
        images=[{"id":f"i{index}","secure_url":f"https://cdn.example/i{index}"} for index in range(MAX_PREVIEW_CACHE_ENTRIES+1)]
        for image in images[:MAX_PREVIEW_CACHE_ENTRIES]: p.selected_image_id=image["id"]; p._load_preview(image)
        p.selected_image_id="i0"; p._load_preview(images[0]); self.assertEqual(service.preview_bytes.call_count,MAX_PREVIEW_CACHE_ENTRIES)
        p.selected_image_id=images[-1]["id"]; p._load_preview(images[-1]); self.assertNotIn(("a1","i1","https://cdn.example/i1"),p._preview_cache); self.assertIn(("a1","i0","https://cdn.example/i0"),p._preview_cache)
    def test_mutations_invalidate_activity_cache(self):
        view,service,p=self.build(); p.selected_id="a1"; p.selected_activity=ITEM; p._preview_cache[("a1","i1","https://cdn.example/i1")]=b"old"; service.activity.return_value=ITEM
        p.upload_image("one.png"); self.assertFalse(any(key[0]=="a1" for key in p._preview_cache))
        p.selected_id="a1"; p.selected_activity=ITEM; p.images=IMAGES; p.selected_image_id="i1"; p._preview_cache[("a1","i1","https://cdn.example/i1")]=b"old"; view.confirm_image_deletion.return_value=True
        p.delete_image(); self.assertFalse(any(key[0]=="a1" for key in p._preview_cache))
    def test_invalid_decode_is_not_cached(self):
        view,service,p=self.build(); p.selected_id="a1"; p.selected_image_id="i1"; service.preview_bytes.return_value=b"invalid"; view.show_preview.return_value=False
        p._load_preview(IMAGES[0]); self.assertEqual(len(p._preview_cache),0)
    def test_obsolete_preview_never_overwrites_current_selection(self):
        view,service,p=self.build(); p.selected_id="a1"; p.selected_image_id="i1"
        def late_result(url): p.selected_image_id="i2"; p._preview_generation+=1; return b"late"
        service.preview_bytes.side_effect=late_result; p._load_preview(IMAGES[0]); view.show_preview.assert_not_called(); self.assertEqual(len(p._preview_cache),0)
    def test_activity_switch_and_image_switch_discard_stale_results(self):
        for changed_attribute,changed_value in (("selected_id","a2"),("selected_image_id","i2")):
            view,service,p=self.build(); p.selected_id="a1"; p.selected_image_id="i1"
            def late_result(url, presenter=p, attribute=changed_attribute, value=changed_value): setattr(presenter,attribute,value); presenter._preview_generation+=1; return b"late"
            service.preview_bytes.side_effect=late_result; p._load_preview(IMAGES[0]); view.show_preview.assert_not_called(); view.show_preview_error.assert_not_called()
    def test_stale_preview_failure_is_ignored(self):
        view,service,p=self.build(); p.selected_id="a1"; p.selected_image_id="i1"
        def late_failure(url): p.selected_image_id="i2"; p._preview_generation+=1; raise RuntimeError("old failure")
        service.preview_bytes.side_effect=late_failure; p._load_preview(IMAGES[0]); view.show_preview_error.assert_not_called(); view.set_preview_loading.assert_called_once_with(True)
