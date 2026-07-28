from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Session:
    access_token: str
    user_id: str
    email: str
    role: str
    customer_id: str | None = None
    instructor_id: str | None = None

    @classmethod
    def from_login_response(cls, payload: dict) -> "Session":
        user = payload["user"]
        return cls(
            access_token=payload["access_token"],
            user_id=str(user["id"]),
            email=user["email"],
            role=user["role"],
            customer_id=str(user["customer_id"]) if user.get("customer_id") else None,
            instructor_id=str(user["instructor_id"]) if user.get("instructor_id") else None,
        )
