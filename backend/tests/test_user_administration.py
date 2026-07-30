from __future__ import annotations

from datetime import UTC, datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.application.services import user_admin_service as service
from backend.app.application.services import auth_service
from backend.app.core.auth import get_current_user
from backend.app.core.security import hash_password, verify_password
from backend.app.infrastructure.repositories import user_repository as repo
from backend.app.main import app
from backend.app.schemas.user_admin import PasswordResetRequest, UserCreateRequest, UserEmailUpdateRequest, UserResponse


def safe_user(**changes):
    now = datetime.now(UTC)
    value = {"id": uuid4(), "email": "user@example.com", "role": "manager", "is_active": True, "customer_id": None, "customer_name": None, "instructor_id": None, "instructor_name": None, "created_at": now, "updated_at": now}
    value.update(changes); return value


class UserAdministrationTests(TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_request_models_normalize_and_enforce_role_profile_contract(self) -> None:
        customer_id = uuid4(); instructor_id = uuid4()
        self.assertEqual(UserCreateRequest(email=" USER@Example.com ", password="password1", role="manager").email, "user@example.com")
        self.assertEqual(UserCreateRequest(email="c@example.com", password="password1", role="customer", customer_id=customer_id).customer_id, customer_id)
        self.assertEqual(UserCreateRequest(email="i@example.com", password="password1", role="instructor", instructor_id=instructor_id).instructor_id, instructor_id)
        invalid = ({"role":"manager","customer_id":customer_id}, {"role":"customer"}, {"role":"instructor","customer_id":customer_id}, {"role":"customer","customer_id":customer_id,"instructor_id":instructor_id})
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
        self.assertEqual(params, ["%User%", "%User%", "%User%", "customer", False, 25, 50]); self.assertNotIn("password_hash", sql)

    def test_eligible_profiles_are_authoritatively_unlinked_and_unbounded_by_user_pages(self) -> None:
        cur = MagicMock(); cur.fetchall.side_effect = [[{"id":uuid4(),"name":"Customer"}], [{"id":uuid4(),"full_name":"Instructor"}]]
        customers, instructors = repo.list_eligible_profiles(cur)
        self.assertEqual(len(customers), 1); self.assertEqual(len(instructors), 1)
        customer_sql = cur.execute.call_args_list[0].args[0]; instructor_sql = cur.execute.call_args_list[1].args[0]
        self.assertIn("NOT EXISTS", customer_sql); self.assertIn("u.customer_id = c.id", customer_sql); self.assertNotIn("LIMIT", customer_sql)
        self.assertIn("NOT EXISTS", instructor_sql); self.assertIn("u.instructor_id = i.id", instructor_sql); self.assertNotIn("LIMIT", instructor_sql)

    def test_manager_can_list_and_non_managers_are_forbidden(self) -> None:
        client = TestClient(app); self.assertEqual(client.get("/users").status_code, 401); app.dependency_overrides[get_current_user] = lambda: {"id":str(uuid4()),"role":"manager"}
        with patch("backend.app.routers.users.service.list_users", return_value=[safe_user()]):
            response = client.get("/users?role=manager&is_active=true")
        self.assertEqual(response.status_code, 200); self.assertEqual(response.json()["count"], 1); self.assertNotIn("password_hash", response.text)
        for role in ("customer", "instructor"):
            app.dependency_overrides[get_current_user] = lambda role=role: {"id":str(uuid4()),"role":role}
            self.assertEqual(client.get("/users").status_code, 403)

    def test_eligible_profiles_endpoint_is_manager_only_and_safe(self) -> None:
        client = TestClient(app); self.assertEqual(client.get("/users/eligible-profiles").status_code, 401)
        for role in ("customer", "instructor"):
            app.dependency_overrides[get_current_user] = lambda role=role: {"id":str(uuid4()),"role":role}
            self.assertEqual(client.get("/users/eligible-profiles").status_code, 403)
        app.dependency_overrides[get_current_user] = lambda: {"id":str(uuid4()),"role":"manager"}
        with patch("backend.app.routers.users.service.list_eligible_profiles", return_value=([{"id":uuid4(),"name":"Customer"}], [{"id":uuid4(),"full_name":"Instructor"}])):
            response = client.get("/users/eligible-profiles")
        self.assertEqual(response.status_code, 200); self.assertEqual(set(response.json()), {"customers", "instructors"}); self.assertNotIn("password", response.text)

    def test_routes_create_detail_edit_status_reset_and_reject_extra_edit_fields(self) -> None:
        client = TestClient(app); actor = uuid4(); user = safe_user()
        app.dependency_overrides[get_current_user] = lambda: {"id":actor,"role":"manager"}
        with patch("backend.app.routers.users.service.create_user", return_value=user):
            response = client.post("/users", json={"email":"user@example.com","password":"password1","role":"manager"})
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

    def test_profile_validation_requires_existing_active_profile(self) -> None:
        customer_id = uuid4(); payload = UserCreateRequest(email="c@example.com", password="password1", role="customer", customer_id=customer_id); cur = MagicMock()
        with patch.object(repo, "get_customer_profile", return_value=None), self.assertRaises(service.ProfileNotFoundError): service._validate_profile(cur, payload)
        with patch.object(repo, "get_customer_profile", return_value={"id":customer_id,"is_active":False}), self.assertRaises(service.UserConflictError): service._validate_profile(cur, payload)
        with patch.object(repo, "get_customer_profile", return_value={"id":customer_id,"is_active":True}): service._validate_profile(cur, payload)
        instructor_id = uuid4(); instructor = UserCreateRequest(email="i@example.com",password="password1",role="instructor",instructor_id=instructor_id)
        with patch.object(repo,"get_instructor_profile",return_value={"id":instructor_id,"is_active":True}): service._validate_profile(cur,instructor)

    @patch.object(service, "get_connection")
    def test_create_hashes_password_and_returns_safe_user(self, get_connection) -> None:
        connection = MagicMock(); cursor = MagicMock(); get_connection.return_value.__enter__.return_value = connection; connection.cursor.return_value.__enter__.return_value = cursor
        created_id = uuid4(); public = safe_user(id=created_id); cursor.fetchone.side_effect = [{"id":created_id,"email":"m@example.com","password_hash":"secret"}, public]
        payload = UserCreateRequest(email="m@example.com", password="password1", role="manager")
        result = service.create_user(payload); args = cursor.execute.call_args_list[0].args
        self.assertNotEqual(args[1][1], "password1"); self.assertTrue(verify_password("password1", args[1][1])); self.assertNotIn("password_hash", result); connection.commit.assert_called_once()

    @patch.object(service, "get_connection")
    def test_create_customer_and_instructor_with_valid_links(self, get_connection) -> None:
        for role, profile_field, name_field in (("customer","customer_id","name"),("instructor","instructor_id","full_name")):
            with self.subTest(role=role):
                connection=MagicMock(); cursor=MagicMock(); get_connection.return_value.__enter__.return_value=connection; connection.cursor.return_value.__enter__.return_value=cursor
                profile_id=uuid4(); user_id=uuid4(); public=safe_user(id=user_id,role=role,**{profile_field:profile_id, "customer_name" if role=="customer" else "instructor_name":"Profile"})
                cursor.fetchone.side_effect=[{"id":profile_id,name_field:"Profile","is_active":True},{"id":user_id},public]
                payload=UserCreateRequest(email=f"{role}@example.com",password="password1",role=role,**{profile_field:profile_id})
                self.assertEqual(service.create_user(payload)["role"],role); connection.commit.assert_called_once()

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
        for required in ("users_role_profile_check", "lower(email)", "users_customer_unique", "users_instructor_unique"): self.assertIn(required, sql)
        for excluded in ("auth_version", "must_change_password", "user_administration_events"): self.assertNotIn(excluded, sql)
