from __future__ import annotations


NAVIGATION_BY_ROLE = {
    "manager": (
        ("dashboard", "לוח בקרה"),
        ("customers", "לקוחות"),
        ("instructors", "מדריכים"),
        ("activities", "פעילויות"),
        ("bookings", "הזמנות"),
        ("open_events", "אירועים פתוחים"),
    ),
    "instructor": (
        ("dashboard", "לוח בקרה"),
        ("activities", "פעילויות"),
        ("bookings", "האירועים שלי"),
        ("open_events", "אירועים פתוחים"),
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
    return tuple(item for item in items if has_profile or item[0] != "my_profile")
