from unittest import TestCase

from desktop_client.app.services.user_service import UserService


class Api:
    def __init__(self): self.calls = []
    def get(self, path, params=None): self.calls.append(("GET", path, params)); return {"items": [], "count": 0}
    def post(self, path, payload): self.calls.append(("POST", path, payload)); return {}
    def put(self, path, payload): self.calls.append(("PUT", path, payload)); return {}


class UserServiceTests(TestCase):
    def test_uses_only_lean_user_endpoints(self) -> None:
        api = Api(); service = UserService(api)
        service.list_users({"role":"manager"}); service.user("u1"); service.create_user({"email":"a@example.com"}); service.update_email("u1","b@example.com"); service.activate("u1"); service.deactivate("u1"); service.reset_password("u1","password1")
        self.assertEqual(api.calls, [
            ("GET","/users",{"role":"manager"}), ("GET","/users/u1",None),
            ("POST","/users",{"email":"a@example.com"}), ("PUT","/users/u1",{"email":"b@example.com"}),
            ("POST","/users/u1/activate",{}), ("POST","/users/u1/deactivate",{}),
            ("POST","/users/u1/reset-password",{"new_password":"password1"}),
        ])
