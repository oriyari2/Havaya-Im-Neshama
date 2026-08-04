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
        ("dashboard", "לוח בקרה"),
        ("activities", "פעילויות"),
        ("bookings", "האירועים שלי"),
        ("my_profile", "הפרופיל שלי"),
    ),
    "customer": (
        ("dashboard", "לוח בקרה"),
        ("activities", "פעילויות"),
        ("my_bookings", "ההזמנות שלי"),
        ("my_profile", "הפרופיל שלי"),
    ),
}


def navigation_for_role(role: str, *, has_profile: bool = True) -> tuple[tuple[str, str], ...]:
    items = NAVIGATION_BY_ROLE.get(role, ())
    visible_items = tuple(item for item in items if has_profile or item[0] != "my_profile")
    return (*visible_items, ("ai_chat", "יועץ AI")) if visible_items else ()
