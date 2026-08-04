from unittest import TestCase
from unittest.mock import Mock
from desktop_client.app.features.bookings.assignment_service import AssignmentService
class AssignmentServiceTests(TestCase):
    def test_endpoints_and_versions(self):
        a=Mock();s=AssignmentService(a);s.assignments("b");a.get.assert_called_with("/bookings/b/assignments");s.open_event_detail("b");a.get.assert_called_with("/bookings/open-events/b");s.assign("b","ba","i",3);a.post.assert_called_with("/bookings/b/instructors",{"booking_activity_id":"ba","instructor_id":"i","expected_version":3});s.remove("b","ba","i",4);a.delete.assert_called_with("/bookings/b/activities/ba/instructors/i",{"expected_version":4})
