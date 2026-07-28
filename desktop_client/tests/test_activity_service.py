from unittest import TestCase
from unittest.mock import Mock
from desktop_client.app.services.activity_service import ActivityService

class ActivityServiceTests(TestCase):
    def setUp(self): self.api=Mock(); self.service=ActivityService(self.api)
    def test_list_and_detail(self):
        filters={"search":"x","target_audience":"y","season":"s","tag":"t","is_active":False,"limit":25,"offset":50}; self.service.list_activities(filters); self.api.get.assert_called_with("/activities",filters); self.service.activity("a1"); self.api.get.assert_called_with("/activities/a1")
    def test_mutations(self):
        self.service.create_activity({"name":"A"}); self.api.post.assert_called_with("/activities",{"name":"A"}); self.service.update_activity("a1",{"name":"B"}); self.api.put.assert_called_with("/activities/a1",{"name":"B"}); self.service.deactivate_activity("a1"); self.api.delete.assert_called_with("/activities/a1"); self.service.reactivate_activity("a1"); self.api.put.assert_called_with("/activities/a1",{"is_active":True})
