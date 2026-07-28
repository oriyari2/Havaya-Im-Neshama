from unittest import TestCase
from unittest.mock import MagicMock,Mock,patch
from uuid import uuid4
from backend.app.application.services import instructor_service as s
from backend.app.infrastructure.repositories import instructor_repository as r
from backend.app.schemas.instructor import InstructorCreate,InstructorUpdate

class InstructorTests(TestCase):
    def test_list_sql_filters_sort_pagination(self):
        cur=Mock();cur.fetchall.return_value=[];r.list_instructors(cur,search=" Name ",city=" City ",is_active=False,order_by="created_at",limit=10,offset=20);sql,params=cur.execute.call_args.args;self.assertIn("ILIKE",sql);self.assertIn("ORDER BY created_at DESC",sql);self.assertEqual(params[-3:],[False,10,20])
    def test_authorization_and_me_scope(self):
        with self.assertRaises(s.InstructorAccessDeniedError):s.list_instructors(search=None,city=None,is_active=None,order_by="full_name",limit=1,offset=0,current_user={"role":"instructor"})
        with self.assertRaises(s.InstructorAccessDeniedError):s.get_my_profile({"role":"customer"})
    @patch.object(s,"get_connection")
    def test_create_is_business_record_only_atomic_and_duplicate_rolls_back(self,get_conn):
        conn=MagicMock();cur=MagicMock();get_conn.return_value.__enter__.return_value=conn;conn.cursor.return_value.__enter__.return_value=cur;cur.fetchone.side_effect=[None,{"id":uuid4()}]
        s.create_instructor(InstructorCreate(full_name="A",email="a@example.com"));conn.commit.assert_called_once();self.assertNotIn("users",cur.execute.call_args_list[-1].args[0].lower())
        conn.reset_mock();cur.fetchone.side_effect=[{"id":uuid4()}]
        with self.assertRaises(s.InstructorConflictError):s.create_instructor(InstructorCreate(full_name="A",email="a@example.com"))
        conn.rollback.assert_called_once()
    @patch.object(s,"get_connection")
    def test_delete_is_physical_atomic_and_checks_all_history(self,get_conn):
        instructor_id=uuid4();conn=MagicMock();cur=MagicMock();get_conn.return_value.__enter__.return_value=conn;conn.cursor.return_value.__enter__.return_value=cur
        cur.fetchone.side_effect=[{"id":instructor_id},{"has_user":False,"has_assignment_history":False,"has_event_history":False},{"id":instructor_id}]
        s.delete_instructor(instructor_id);sql=" ".join(x.args[0] for x in cur.execute.call_args_list)
        self.assertIn("FOR UPDATE",sql);self.assertIn("booking_instructors",sql);self.assertIn("event_data",sql);self.assertIn("DELETE FROM instructors",sql);self.assertNotIn("UPDATE instructors",sql);conn.commit.assert_called_once()
    @patch.object(s,"get_connection")
    def test_delete_dependency_conflict_rolls_back_before_delete(self,get_conn):
        for dependency in ("has_user","has_assignment_history","has_event_history"):
            with self.subTest(dependency=dependency):
                instructor_id=uuid4();conn=MagicMock();cur=MagicMock();get_conn.return_value.__enter__.return_value=conn;conn.cursor.return_value.__enter__.return_value=cur
                flags={"has_user":False,"has_assignment_history":False,"has_event_history":False};flags[dependency]=True;cur.fetchone.side_effect=[{"id":instructor_id},flags]
                with self.assertRaises(s.InstructorDeleteConflictError):s.delete_instructor(instructor_id)
                sql=" ".join(x.args[0] for x in cur.execute.call_args_list);self.assertNotIn("DELETE FROM instructors",sql);conn.rollback.assert_called_once();conn.commit.assert_not_called()
    def test_response_schema_never_exposes_password(self):
        self.assertNotIn("password_hash",s.__dict__);self.assertNotIn("password_hash",InstructorCreate.model_fields);self.assertNotIn("password_hash",InstructorUpdate.model_fields)
