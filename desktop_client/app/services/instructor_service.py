from desktop_client.app.api.client import ApiClient
class InstructorService:
    def __init__(self,api_client:ApiClient):self.api_client=api_client
    def list_instructors(self,filters):return self.api_client.get("/instructors",filters)
    def instructor(self,instructor_id):return self.api_client.get(f"/instructors/{instructor_id}")
    def my_profile(self):return self.api_client.get("/instructors/me")
    def create_instructor(self,payload):return self.api_client.post("/instructors",payload)
    def update_instructor(self,instructor_id,payload):return self.api_client.put(f"/instructors/{instructor_id}",payload)
    def activate(self,instructor_id):return self.api_client.post(f"/instructors/{instructor_id}/activate",{})
    def deactivate(self,instructor_id):return self.api_client.post(f"/instructors/{instructor_id}/deactivate",{})
    def reset_password(self,instructor_id,new_password):self.api_client.post(f"/instructors/{instructor_id}/reset-password",{"new_password":new_password})
    def invalidate_list(self,filters):self.api_client.invalidate_cached_get("/instructors",filters)
