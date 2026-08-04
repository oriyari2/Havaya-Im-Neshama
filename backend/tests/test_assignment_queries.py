from unittest import TestCase
from unittest.mock import MagicMock,patch
from uuid import uuid4
from backend.app.application.bookings import assignment_query_handlers as h
from backend.app.application.bookings.query_handlers import BookingAccessDeniedError
class AssignmentQueryTests(TestCase):
    def test_customer_denied(self):
        with self.assertRaises(BookingAccessDeniedError):h.get_assignments(uuid4(),{"role":"customer"})
        with self.assertRaises(BookingAccessDeniedError):h.get_open_event_detail(uuid4(),{"role":"customer"})
    @patch.object(h,"get_connection")
    def test_manager_model_has_ids_version_active_only_and_required_state(self,g):
        bid,baid,aid,iid=uuid4(),uuid4(),uuid4(),uuid4();conn=MagicMock();cur=MagicMock();g.return_value.__enter__.return_value=conn;conn.cursor.return_value.__enter__.return_value=cur;cur.fetchone.return_value={"booking_id":bid,"version":4,"requires_instructor":True};cur.fetchall.side_effect=[[{"booking_activity_id":baid,"activity_id":aid,"activity_name":"A","assignment_required":False}],[{"booking_activity_id":baid,"instructor_id":iid,"instructor_name":"I","instructor_city":"C","assigned_at":"2026-01-01"}],[]];x=h.get_assignments(bid,{"role":"manager"});self.assertEqual(x["version"],4);self.assertEqual(x["activities"][0]["assignments"][0]["instructor_id"],iid)
    def test_assignment_sql_filters_inactive_rows(self):
        from backend.app.infrastructure.repositories import booking_assignment_repository as r
        cur=MagicMock();cur.fetchall.return_value=[];r.list_active_assignments(cur,uuid4());self.assertIn("bi.active=true",cur.execute.call_args.args[0])
    def test_safe_schema_has_no_sensitive_fields(self):
        from backend.app.schemas.booking_assignment import OpenEventDetailResponse,BookingAssignmentsResponse
        for field in ("customer_id","agreed_price","notes","participant_count"):self.assertNotIn(field,OpenEventDetailResponse.model_fields);self.assertNotIn(field,BookingAssignmentsResponse.model_fields)
    def test_new_booking_event_carries_stable_activity_id_and_projection_upsert(self):
        from backend.app.domain.bookings.events import booking_created
        from backend.app.domain.bookings.aggregate import BookingAggregate
        from backend.app.infrastructure.repositories.booking_projection_repository import upsert_default_booking_activity
        from datetime import datetime,UTC
        from decimal import Decimal
        bid,baid,aid,cid=uuid4(),uuid4(),uuid4(),uuid4();event=booking_created(customer_id=cid,activity_id=aid,booking_activity_id=baid,event_at=datetime.now(UTC),city=None,venue=None,participant_count=1,agreed_price=Decimal("0"),status="NEW",requires_instructor=True,notes=None);aggregate=BookingAggregate.replay(bid,[{"event_type":"BookingCreated","event_data":event.payload(),"aggregate_version":1}]);self.assertEqual(aggregate.booking_activity_id,baid);cur=MagicMock();upsert_default_booking_activity(cur,baid,bid,aid,aggregate.event_at,1);self.assertIn("INSERT INTO booking_activities",cur.execute.call_args.args[0])
