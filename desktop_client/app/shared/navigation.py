from __future__ import annotations


NAVIGATION_BY_ROLE = {
    "manager": (
        ("dashboard", "לוח בקרה"),
        ("customers", "לקוחות"),
        ("instructors", "מדריכים"),
        ("users", "מנהלים"),
        ("bookings", "הזמנות"),
        ("activities", "פעילויות"),
        ("knowledge", "ניהול ידע"),
    ),
    "instructor": (
        ("bookings", "האירועים שלי"),
        ("activities", "פעילויות"),
        ("my_profile", "הפרופיל שלי"),
    ),
    "customer": (
        ("my_bookings", "ההזמנות שלי"),
        ("activities", "פעילויות"),
        ("my_profile", "הפרופיל שלי"),
    ),
}

DEFAULT_PAGE_BY_ROLE = {
    "manager": "dashboard",
    "instructor": "bookings",
    "customer": "my_bookings",
}


def navigation_for_role(role: str, *, has_profile: bool = True) -> tuple[tuple[str, str], ...]:
    items = NAVIGATION_BY_ROLE.get(role, ())
    visible_items = tuple(item for item in items if has_profile or item[0] != "my_profile")
    return (*visible_items, ("ai_chat", "יועץ AI")) if visible_items else ()


def default_page_for_role(role: str) -> str | None:
    return DEFAULT_PAGE_BY_ROLE.get(role)
