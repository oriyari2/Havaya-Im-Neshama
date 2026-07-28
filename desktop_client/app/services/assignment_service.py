from desktop_client.app.api.client import ApiClient
class AssignmentService:
    def __init__(self,api_client:ApiClient):self.api_client=api_client
    def assignments(self,booking_id):return self.api_client.get(f"/bookings/{booking_id}/assignments")
    def open_event_detail(self,booking_id):return self.api_client.get(f"/bookings/open-events/{booking_id}")
    def assign(self,booking_id,booking_activity_id,instructor_id,expected_version):return self.api_client.post(f"/bookings/{booking_id}/instructors",{"booking_activity_id":booking_activity_id,"instructor_id":instructor_id,"expected_version":expected_version})
    def remove(self,booking_id,booking_activity_id,instructor_id,expected_version):return self.api_client.delete(f"/bookings/{booking_id}/activities/{booking_activity_id}/instructors/{instructor_id}",{"expected_version":expected_version})
