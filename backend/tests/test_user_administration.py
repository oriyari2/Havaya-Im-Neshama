from __future__ import annotations

from datetime import UTC, datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from pydantic import ValidationError
from psycopg import IntegrityError

from backend.app.application.services import user_admin_service as service
from backend.app.application.services import auth_service
from backend.app.core.auth import get_current_user
from backend.app.core.security import hash_password, verify_password
from backend.app.infrastructure.repositories import user_repository as repo
from backend.app.main import app
from backend.app.schemas.user_admin import PasswordResetRequest, UserCreateRequest, UserEmailUpdateRequest, UserResponse


def safe_user(**changes):
    now = datetime.now(UTC)
    value = {"id": uuid4(), "email": "user@example.com", "role": "manager", "display_name": "Manager", "is_active": True, "customer_id": None, "customer_name": None, "instructor_id": None, "instructor_name": None, "created_at": now, "updated_at": now}
    value.update(changes); return value


class UserAdministrationTests(TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_request_models_normalize_and_enforce_role_profile_contract(self) -> None:
        manager=UserCreateRequest(email=" USER@Example.com ", password="password1", role="manager",manager_name=" Manager "); self.assertEqual((manager.email,manager.manager_name),("user@example.com","Manager"))
        customer = UserCreateRequest(email="c@example.com", password="password1", role="customer", customer_name=" Customer ", customer_type=" School ", customer_city=" Haifa ", contact_name=" Contact ", contact_phone=" 050 ")
        self.assertEqual((customer.email, customer.customer_name, customer.customer_type, customer.customer_city, customer.contact_name, customer.contact_phone), ("c@example.com", "Customer", "School", "Haifa", "Contact", "050"))
        instructor = UserCreateRequest(email="i@example.com", password="password1", role="instructor", instructor_name=" Instructor ", instructor_phone=" 051 ", instructor_city=" Jerusalem ")
        self.assertEqual((instructor.email, instructor.instructor_name, instructor.instructor_phone, instructor.instructor_city), ("i@example.com", "Instructor", "051", "Jerusalem"))
        minimal_customer = UserCreateRequest(email="minimal-c@example.com", password="password1", role="customer", customer_name="Customer")
        minimal_instructor = UserCreateRequest(email="minimal-i@example.com", password="password1", role="instructor", instructor_name="Instructor")
        self.assertIsNone(minimal_customer.contact_name); self.assertIsNone(minimal_instructor.instructor_city)
        invalid = ({"role":"manager"}, {"role":"manager","manager_name":"M","customer_name":"x"}, {"role":"customer"}, {"role":"customer","customer_name":"x","contact_name":"y"}, {"role":"instructor"}, {"role":"instructor","instructor_name":"x","customer_name":"y"}, {"role":"customer","customer_id":str(uuid4())})
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValidationError): UserCreateRequest(email="x@example.com", password="password1", **values)

    def test_edit_schema_is_email_only_and_secret_fields_are_not_public(self) -> None:
        self.assertEqual(UserEmailUpdateRequest(email=" NEW@Example.com ").model_dump(), {"email":"new@example.com"})
        for forbidden in ({"email":"x@example.com","role":"manager"}, {"email":"x@example.com","customer_id":str(uuid4())}):
            with self.assertRaises(ValidationError): UserEmailUpdateRequest(**forbidden)
        fields = UserResponse.model_fields
        for secret in ("password", "password_hash", "access_token", "token"):
            self.assertNotIn(secret, fields)

    def test_repository_list_is_parameterized_filtered_and_safe(self) -> None:
        cur = MagicMock(); cur.fetchall.return_value = []
        repo.list_users(cur, search=" User ", role="customer", is_active=False, limit=25, offset=50)
        sql, params = cur.execute.call_args.args
        self.assertIn("u.email ILIKE %s", sql); self.assertIn("c.name ILIKE %s", sql); self.assertIn("i.full_name ILIKE %s", sql); self.assertIn("u.role = %s", sql); self.assertIn("u.is_active = %s", sql)
        self.assertEqual(params, ["%User%", "%User%", "%User%", "%User%", "customer", False, 25, 50]); self.assertNotIn("password_hash", sql)

    def test_manager_can_list_and_non_managers_are_forbidden(self) -> None:
        client = TestClient(app); self.assertEqual(client.get("/users").status_code, 401); app.dependency_overrides[get_current_user] = lambda: {"id":str(uuid4()),"role":"manager"}
        with patch("backend.app.routers.users.service.list_users", return_value=[safe_user()]):
            response = client.get("/users?role=manager&is_active=true")
        self.assertEqual(response.status_code, 200); self.assertEqual(response.json()["count"], 1); self.assertNotIn("password_hash", response.text)
        for role in ("customer", "instructor"):
            app.dependency_overrides[get_current_user] = lambda role=role: {"id":str(uuid4()),"role":role}
            self.assertEqual(client.get("/users").status_code, 403)

    def test_routes_create_detail_edit_status_reset_and_reject_extra_edit_fields(self) -> None:
        client = TestClient(app); actor = uuid4(); user = safe_user()
        app.dependency_overrides[get_current_user] = lambda: {"id":actor,"role":"manager"}
        with patch("backend.app.routers.users.service.create_user", return_value=user):
            response = client.post("/users", json={"email":"user@example.com","password":"password1","role":"manager","manager_name":"Manager"})
            self.assertEqual(response.status_code, 201)
        with patch("backend.app.routers.users.service.get_user", return_value=user): self.assertEqual(client.get(f"/users/{user['id']}").status_code, 200)
        with patch("backend.app.routers.users.service.update_email", return_value={**user,"email":"new@example.com"}): self.assertEqual(client.put(f"/users/{user['id']}", json={"email":"new@example.com"}).status_code, 200)
        self.assertEqual(client.put(f"/users/{user['id']}", json={"email":"new@example.com","role":"customer"}).status_code, 422)
        with patch("backend.app.routers.users.service.set_active", return_value={**user,"is_active":False}) as action:
            self.assertEqual(client.post(f"/users/{user['id']}/deactivate", json={}).status_code, 200); action.assert_called_once()
        with patch("backend.app.routers.users.service.set_active", return_value={**user,"is_active":True}) as action:
            self.assertEqual(client.post(f"/users/{user['id']}/activate", json={}).status_code, 200); action.assert_called_once()
        with patch("backend.app.routers.users.service.reset_password") as reset:
            self.assertEqual(client.post(f"/users/{user['id']}/reset-password", json={"new_password":"newpass123"}).status_code, 204); reset.assert_called_once()

    @patch.object(service, "get_connection")
    def test_create_hashes_password_and_returns_safe_user(self, get_connection) -> None:
        connection = MagicMock(); cursor = MagicMock(); get_connection.return_value.__enter__.return_value = connection; connection.cursor.return_value.__enter__.return_value = cursor
        created_id = uuid4(); public = safe_user(id=created_id); cursor.fetchone.side_effect = [{"id":created_id,"email":"m@example.com","password_hash":"secret"}, public]
        payload = UserCreateRequest(email="m@example.com", password="password1", role="manager",manager_name="Manager")
        result = service.create_user(payload); args = cursor.execute.call_args_list[0].args
        self.assertNotEqual(args[1][1], "password1"); self.assertTrue(verify_password("password1", args[1][1])); self.assertNotIn("password_hash", result); connection.commit.assert_called_once()

    @patch.object(service, "get_connection")
    def test_create_customer_atomically_creates_customer_contact_and_linked_user(self, get_connection) -> None:
        connection=MagicMock(); cursor=MagicMock(); get_connection.return_value.__enter__.return_value=connection; connection.cursor.return_value.__enter__.return_value=cursor
        customer_id=uuid4(); user_id=uuid4(); public=safe_user(id=user_id,role="customer",customer_id=customer_id,customer_name="Customer",customer_email="customer@example.com",contact_name="Contact",contact_phone="050")
        payload=UserCreateRequest(email="customer@example.com",password="password1",role="customer",customer_name="Customer",customer_type="School",customer_city="Haifa",contact_name="Contact",contact_phone="050")
        with patch.object(service.customer_repository,"create_customer",return_value={"id":customer_id}) as create_customer, patch.object(service.customer_repository,"create_contact") as create_contact, patch.object(repo,"create_user",return_value={"id":user_id}) as create_user, patch.object(repo,"get_safe_user",return_value=public):
            result=service.create_user(payload)
        self.assertEqual(create_customer.call_args.args[1]["email"],payload.email); self.assertEqual((create_customer.call_args.args[1]["customer_type"],create_customer.call_args.args[1]["city"]),("School","Haifa")); self.assertEqual(create_contact.call_args.args[2]["full_name"],"Contact"); self.assertEqual(create_contact.call_args.args[2]["phone"],"050")
        self.assertEqual(create_user.call_args.kwargs["customer_id"],customer_id); self.assertIsNone(create_user.call_args.kwargs["instructor_id"]); self.assertEqual(result["customer_email"],payload.email); connection.commit.assert_called_once()

    @patch.object(service, "get_connection")
    def test_create_instructor_atomically_creates_instructor_and_linked_user(self, get_connection) -> None:
        connection=MagicMock(); cursor=MagicMock(); get_connection.return_value.__enter__.return_value=connection; connection.cursor.return_value.__enter__.return_value=cursor
        instructor_id=uuid4(); user_id=uuid4(); public=safe_user(id=user_id,role="instructor",instructor_id=instructor_id,instructor_name="Instructor",instructor_email="instructor@example.com",instructor_phone="051")
        payload=UserCreateRequest(email="instructor@example.com",password="password1",role="instructor",instructor_name="Instructor",instructor_phone="051",instructor_city="Jerusalem")
        with patch.object(service.instructor_repository,"get_by_email",return_value=None), patch.object(service.instructor_repository,"create_instructor",return_value={"id":instructor_id}) as create_instructor, patch.object(repo,"create_user",return_value={"id":user_id}) as create_user, patch.object(repo,"get_safe_user",return_value=public):
            result=service.create_user(payload)
        data=create_instructor.call_args.args[1]; self.assertEqual((data["full_name"],data["email"],data["phone"],data["city"]),("Instructor",payload.email,"051","Jerusalem")); self.assertEqual(create_user.call_args.kwargs["instructor_id"],instructor_id); self.assertIsNone(create_user.call_args.kwargs["customer_id"]); self.assertEqual(result["instructor_email"],payload.email); connection.commit.assert_called_once()

    @patch.object(service, "get_connection")
    def test_minimal_customer_account_skips_optional_contact_atomically(self, get_connection) -> None:
        connection=MagicMock(); cursor=MagicMock(); get_connection.return_value.__enter__.return_value=connection; connection.cursor.return_value.__enter__.return_value=cursor
        customer_id=uuid4(); user_id=uuid4(); public=safe_user(id=user_id,role="customer",customer_id=customer_id,customer_name="Customer",customer_email="customer@example.com")
        payload=UserCreateRequest(email="customer@example.com",password="password1",role="customer",customer_name="Customer")
        with patch.object(service.customer_repository,"create_customer",return_value={"id":customer_id}) as create_customer, patch.object(service.customer_repository,"create_contact") as create_contact, patch.object(repo,"create_user",return_value={"id":user_id}) as create_user, patch.object(repo,"get_safe_user",return_value=public):
            result=service.create_user(payload)
        create_contact.assert_not_called(); self.assertIsNone(create_customer.call_args.args[1]["city"]); self.assertEqual(create_user.call_args.kwargs["customer_id"],customer_id); self.assertEqual(result["customer_id"],customer_id); connection.commit.assert_called_once()

    @patch.object(service, "get_connection")
    def test_profile_creation_rolls_back_when_user_creation_fails(self, get_connection) -> None:
        connection=MagicMock(); cursor=MagicMock(); get_connection.return_value.__enter__.return_value=connection; connection.cursor.return_value.__enter__.return_value=cursor
        payload=UserCreateRequest(email="customer@example.com",password="password1",role="customer",customer_name="Customer",customer_type="School",customer_city="Haifa",contact_name="Contact",contact_phone="050")
        with patch.object(service.customer_repository,"create_customer",return_value={"id":uuid4()}), patch.object(service.customer_repository,"create_contact"), patch.object(repo,"create_user",side_effect=IntegrityError("duplicate")), self.assertRaises(service.UserConflictError): service.create_user(payload)
        connection.rollback.assert_called_once(); connection.commit.assert_not_called()

    @patch.object(service, "get_connection")
    def test_email_edit_keeps_customer_or_instructor_email_equal_to_login(self, get_connection) -> None:
        for role, link_field in (("customer","customer_id"),("instructor","instructor_id")):
            with self.subTest(role=role):
                connection=MagicMock(); cursor=MagicMock(); get_connection.return_value.__enter__.return_value=connection; connection.cursor.return_value.__enter__.return_value=cursor
                user_id=uuid4(); profile_id=uuid4(); existing={"id":user_id,"role":role,"customer_id":profile_id if role=="customer" else None,"instructor_id":profile_id if role=="instructor" else None}; public=safe_user(id=user_id,role=role,email="new@example.com",**{link_field:profile_id})
                with patch.object(repo,"get_user_by_id",return_value=existing), patch.object(repo,"update_user_email") as update_user, patch.object(repo,"get_safe_user",return_value=public), patch.object(service.customer_repository,"update_customer") as update_customer, patch.object(service.instructor_repository,"get_by_email",return_value=None), patch.object(service.instructor_repository,"update_instructor") as update_instructor:
                    service.update_email(user_id,UserEmailUpdateRequest(email="new@example.com"))
                update_user.assert_called_once_with(cursor,user_id,"new@example.com")
                if role=="customer": update_customer.assert_called_once_with(cursor,profile_id,{"email":"new@example.com"})
                else: update_instructor.assert_called_once_with(cursor,profile_id,{"email":"new@example.com"})
                connection.commit.assert_called_once()

    def test_integrity_constraints_map_to_safe_conflicts(self) -> None:
        class Diag:
            def __init__(self, name): self.constraint_name=name
        class Error:
            def __init__(self, name): self.diag=Diag(name)
        self.assertIn("Customer",str(service._translate_integrity_error(Error("idx_users_customer_unique"))))
        self.assertIn("Instructor",str(service._translate_integrity_error(Error("idx_users_instructor_unique"))))
        self.assertIn("Email",str(service._translate_integrity_error(Error("idx_users_email_normalized_unique"))))

    @patch.object(service, "get_connection")
    def test_self_deactivation_is_rejected_without_database_write(self, get_connection) -> None:
        user_id = uuid4()
        with self.assertRaises(service.UserConflictError): service.set_active(user_id, False, {"id":user_id,"role":"manager"})
        get_connection.assert_not_called()

    @patch.object(service, "get_connection")
    def test_status_change_and_missing_user(self, get_connection) -> None:
        connection = MagicMock(); cursor = MagicMock(); get_connection.return_value.__enter__.return_value = connection; connection.cursor.return_value.__enter__.return_value = cursor
        user_id = uuid4(); existing = {"id":user_id,"role":"manager","is_active":True,"customer_id":None,"instructor_id":None}; public = safe_user(id=user_id,is_active=False); cursor.fetchone.side_effect=[existing,{"id":user_id},public]
        self.assertFalse(service.set_active(user_id, False, {"id":uuid4(),"role":"manager"})["is_active"]); connection.commit.assert_called_once()
        cursor.fetchone.side_effect=[None]
        with self.assertRaises(service.UserNotFoundError): service.set_active(uuid4(), True, {"id":uuid4(),"role":"manager"})

    @patch.object(service, "get_connection")
    def test_reset_password_replaces_hash_and_old_password_fails(self, get_connection) -> None:
        connection = MagicMock(); cursor = MagicMock(); get_connection.return_value.__enter__.return_value = connection; connection.cursor.return_value.__enter__.return_value = cursor
        user_id = uuid4(); cursor.fetchone.side_effect=[{"id":user_id},{"id":user_id}]
        service.reset_password(user_id, PasswordResetRequest(new_password="newpass123")); stored = cursor.execute.call_args_list[1].args[1][0]
        self.assertFalse(verify_password("oldpass123", stored)); self.assertTrue(verify_password("newpass123", stored)); connection.commit.assert_called_once()

    @patch.object(auth_service, "get_connection")
    def test_inactive_login_rejected_and_active_login_succeeds(self, get_connection) -> None:
        connection=MagicMock(); cursor=MagicMock(); get_connection.return_value.__enter__.return_value=connection; connection.cursor.return_value.__enter__.return_value=cursor
        user=safe_user(); user["password_hash"]=hash_password("password1"); cursor.fetchone.return_value={**user,"is_active":False}
        with self.assertRaises(auth_service.InvalidCredentialsError): auth_service.login(user["email"],"password1")
        cursor.fetchone.return_value=user; token, public=auth_service.login(user["email"],"password1"); self.assertTrue(token); self.assertNotIn("password_hash",public)

    def test_schema_contains_only_lean_constraints(self) -> None:
        from backend.app.db.schema import ALTER_TABLE_SQL, CREATE_INDEX_SQL
        sql = " ".join([*ALTER_TABLE_SQL, *CREATE_INDEX_SQL]).lower()
        for required in ("display_name", "users_role_profile_check", "lower(email)", "users_customer_unique", "users_instructor_unique"): self.assertIn(required, sql)
        for excluded in ("auth_version", "must_change_password", "user_administration_events"): self.assertNotIn(excluded, sql)
