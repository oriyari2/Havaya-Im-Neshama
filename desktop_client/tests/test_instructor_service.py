from unittest import TestCase
from unittest.mock import Mock
from desktop_client.app.services.instructor_service import InstructorService
class InstructorServiceTests(TestCase):
    def test_all_endpoints(self):
        a=Mock();s=InstructorService(a);q={"search":"x","city":"y","is_active":False,"order_by":"created_at","limit":2,"offset":1};s.list_instructors(q);a.get.assert_called_with("/instructors",q);s.instructor("i");a.get.assert_called_with("/instructors/i");s.my_profile();a.get.assert_called_with("/instructors/me");s.create_instructor({"full_name":"A"});a.post.assert_called_with("/instructors",{"full_name":"A"});s.update_instructor("i",{"city":"C"});a.put.assert_called_with("/instructors/i",{"city":"C"});s.delete_instructor("i");a.delete.assert_called_with("/instructors/i")
