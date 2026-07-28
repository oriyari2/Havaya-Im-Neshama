from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal

from psycopg import Connection

from backend.app.domain.bookings.status import BookingStatus

from backend.app.db.connection import get_connection
from backend.app.db.init_db import seed_demo_users


DEMO_MARKER = "נתוני דמו - חוויה עם נשמה"
DEMO_BASE_UUID = "00000000-0000-4000-8000"
DEMO_USER_EMAILS = (
    "manager@example.com",
    "instructor@example.com",
    "customer@example.com",
)


def demo_id(group: int, number: int) -> str:
    return f"{DEMO_BASE_UUID}-{group:04d}{number:08d}"


def demo_ids() -> list[str]:
    return [demo_id(group, number) for group in range(1, 13) for number in range(1, 201)]


@dataclass(frozen=True)
class ExternalReference:
    table: str
    relationship: str
    count: int


class DemoSeedSafetyError(RuntimeError):
    def __init__(self, references: list[ExternalReference]) -> None:
        self.references = references
        details = "; ".join(
            f"{reference.table}.{reference.relationship}: {reference.count} external row(s)"
            for reference in references
        )
        super().__init__(f"Demo refresh aborted because external references were found: {details}")


CUSTOMERS = [
    {
        "id": demo_id(1, 1),
        "name": "בית ספר נועם ירושלים",
        "customer_type": "בית ספר",
        "city": "ירושלים",
        "address": "רחוב הדמו 1",
        "phone": "02-0000001",
        "email": "noam-demo@example.com",
        "notes": f"{DEMO_MARKER}. מוסד חינוכי יסודי לקבוצות בנים.",
    },
    {
        "id": demo_id(1, 2),
        "name": 'מתנ"ס גבעת שמואל',
        "customer_type": 'מתנ"ס',
        "city": "גבעת שמואל",
        "address": "שדרות הקהילה 12",
        "phone": "03-0000002",
        "email": "matnas-demo@example.com",
        "notes": f"{DEMO_MARKER}. פעילויות קהילתיות לילדים ונוער.",
    },
    {
        "id": demo_id(1, 3),
        "name": "עיריית מודיעין - אגף תרבות תורנית",
        "customer_type": "עירייה",
        "city": "מודיעין",
        "address": "כיכר העיר 5",
        "phone": "08-0000003",
        "email": "modiin-demo@example.com",
        "notes": f"{DEMO_MARKER}. אירועי שיא למשפחות ולקהילה.",
    },
    {
        "id": demo_id(1, 4),
        "name": "אולפנת אורות",
        "customer_type": "אולפנה",
        "city": "בית שמש",
        "address": "רחוב האור 18",
        "phone": "02-0000004",
        "email": "orot-demo@example.com",
        "notes": f"{DEMO_MARKER}. ימי חסד וגיבוש לתלמידות.",
    },
    {
        "id": demo_id(1, 5),
        "name": "ישיבת בני עקיבא רעננה",
        "customer_type": "ישיבה",
        "city": "רעננה",
        "address": "רחוב החלוצים 7",
        "phone": "09-0000005",
        "email": "yeshiva-demo@example.com",
        "notes": f"{DEMO_MARKER}. פעילות חברתית לתלמידי חטיבה ותיכון.",
    },
    {
        "id": demo_id(1, 6),
        "name": "קייטנת קיץ בית שמש",
        "customer_type": "קייטנה",
        "city": "בית שמש",
        "address": "פארק העיר 3",
        "phone": "02-0000006",
        "email": "camp-demo@example.com",
        "notes": f"{DEMO_MARKER}. קייטנת קיץ רב גילאית.",
    },
    {
        "id": demo_id(1, 7),
        "name": "תלמוד תורה דרכי אבות",
        "customer_type": "בית ספר",
        "city": "פתח תקווה",
        "address": "רחוב האבות 22",
        "phone": "03-0000007",
        "email": "darchei-avot-demo@example.com",
        "notes": f"{DEMO_MARKER}. פעילות ערכית לכיתות ד-ח.",
    },
]


CONTACTS = [
    (demo_id(2, 1), demo_id(1, 1), "רבקה לוי", "רכזת חברתית", "050-0000001", "demo1@example.com", True),
    (demo_id(2, 2), demo_id(1, 1), "אליהו כהן", "מנהל בית ספר", "052-0000002", "demo2@example.com", False),
    (demo_id(2, 3), demo_id(1, 2), "נעמה ישראלי", "רכזת תרבות", "054-0000003", "demo3@example.com", True),
    (demo_id(2, 4), demo_id(1, 3), "יוסי בן דוד", "רכז תרבות", "050-0000004", "demo4@example.com", True),
    (demo_id(2, 5), demo_id(1, 4), "אפרת מזרחי", "מזכירות", "052-0000005", "demo5@example.com", True),
    (demo_id(2, 6), demo_id(1, 5), "שמואל פרידמן", "רכז חברתי", "054-0000006", "demo6@example.com", True),
    (demo_id(2, 7), demo_id(1, 6), "חני אברהם", "מנהלת קייטנה", "050-0000007", "demo7@example.com", True),
    (demo_id(2, 8), demo_id(1, 7), "דוד שמיר", "מנהל תלמוד תורה", "052-0000008", "demo8@example.com", True),
    (demo_id(2, 9), demo_id(1, 3), "תהילה שטרן", "מזכירות", "054-0000009", "demo9@example.com", False),
]


INSTRUCTORS = [
    (demo_id(3, 1), "מיכל כהן", "050-1000001", "michal-demo@example.com", "ירושלים", "מדריכה ותיקה לפעילויות לייזר ותחנות"),
    (demo_id(3, 2), "שירה לוי", "052-1000002", "shira-demo@example.com", "בית שמש", "מתמחה בסדנאות יצירה"),
    (demo_id(3, 3), "תמר ישראלי", "054-1000003", "tamar-demo@example.com", "מודיעין", "מדריכת חידונים ומשחקי קבוצה"),
    (demo_id(3, 4), "הדס אברהם", "050-1000004", "hadas-demo@example.com", "גבעת שמואל", "מובילת אירועי משפחות"),
    (demo_id(3, 5), "יעל מזרחי", "052-1000005", "yael-demo@example.com", "רעננה", "מדריכת סדנאות וחגים"),
    (demo_id(3, 6), "נועה שפירא", "054-1000006", "noa-demo@example.com", "פתח תקווה", "אחראית ציוד והפעלה בשטח"),
]


ACTIVITIES = [
    (demo_id(4, 1), "תפוס את האור", "פעילות אתגרית עם ציוד לייזר, משימות קבוצתיות וניקוד.", 90, 20, 120, 1200, '1,200 ש"ח עד 60 משתתפים; 15 ש"ח לכל משתתף נוסף.', 45, 30),
    (demo_id(4, 2), "מירוץ הצופן", "משחק תחנות לפענוח כתבי חידה וצפנים.", 75, 25, 100, 1500, '1,500 ש"ח עד 80 משתתפים.', 35, 25),
    (demo_id(4, 3), "חידון שלטים", "חידון שלטים קבוצתי עם שאלות ידע, זריזות ושיתוף פעולה.", 60, 15, 90, 900, '900 ש"ח למפגש.', 25, 20),
    (demo_id(4, 4), "סדנת תיק בעיצוב אישי", "סדנת יצירה שבה כל משתתף מעצב תיק אישי.", 80, 20, 120, 1200, '32 ש"ח למשתתף; מינימום 1,200 ש"ח.', 40, 30),
    (demo_id(4, 5), "קישוט סוכה על קנבס", "סדנת יצירה לחג הסוכות על קנבס אישי.", 70, 20, 150, 1400, '34 ש"ח למשתתף עד 100; 28 ש"ח מעל 100.', 35, 25),
]


INSTRUCTION_NOTES = [
    (demo_id(5, 1), demo_id(4, 1), "טעינת ציוד", "לבדוק שכל ערכות הלייזר טעונות ערב קודם.", 1),
    (demo_id(5, 2), demo_id(4, 1), "גיבוי", "להביא סוללות גיבוי ומטענים.", 2),
    (demo_id(5, 3), demo_id(4, 1), "בטיחות", "לוודא שיש שטח פתוח ובטיחותי לפעילות.", 3),
    (demo_id(5, 4), demo_id(4, 4), "עמדות חומרים", "להכין מראש עמדת חומרים לכל קבוצה.", 1),
    (demo_id(5, 5), demo_id(4, 4), "בדיקת מלאי", "לבדוק שיש מספיק טושים, שבלונות ותיקים.", 2),
    (demo_id(5, 6), demo_id(4, 4), "תוצרים רזרביים", "לשמור כמה תוצרים רזרביים למקרה של תקלה.", 3),
]


INVENTORY_ITEMS = [
    (demo_id(6, 1), "ערכת לייזר", "ציוד פעילות", "ערכה", 24, 24, "מחסן ראשי", True),
    (demo_id(6, 2), "מטען לערכת לייזר", "ציוד חשמל", "יחידה", 24, 24, "מחסן ראשי", False),
    (demo_id(6, 3), "סוללות נטענות", "ציוד חשמל", "סט", 40, 40, "ארון טעינה", True),
    (demo_id(6, 4), "שלטי חידון", "ציוד משחק", "שלט", 20, 20, "מדף משחקים", False),
    (demo_id(6, 5), "כרטיסי שאלות", "ציוד משחק", "חבילה", 15, 15, "מדף משחקים", False),
    (demo_id(6, 6), "תיקי בד להדפסה", "חומרי יצירה", "יחידה", 300, 300, "מחסן יצירה", False),
    (demo_id(6, 7), "טושים לבד", "חומרי יצירה", "קופסה", 35, 35, "מחסן יצירה", False),
    (demo_id(6, 8), "שבלונות עיצוב", "חומרי יצירה", "סט", 25, 25, "מחסן יצירה", False),
    (demo_id(6, 9), "מעטפות משימה", "ציוד משחק", "מעטפה", 200, 200, "מדף משחקים", False),
    (demo_id(6, 10), "כרטיסי צופן", "ציוד משחק", "חבילה", 30, 30, "מדף משחקים", False),
    (demo_id(6, 11), "קנבסים לסוכה", "חומרי יצירה", "יחידה", 250, 250, "מחסן יצירה", False),
    (demo_id(6, 12), "רמקול נייד", "ציוד כללי", "יחידה", 4, 4, "מחסן ראשי", True),
    (demo_id(6, 13), "כבל מאריך", "ציוד כללי", "יחידה", 12, 12, "מחסן ראשי", False),
    (demo_id(6, 14), "ארגז ציוד כללי", "ציוד כללי", "ארגז", 8, 8, "מחסן ראשי", False),
]


ACTIVITY_REQUIREMENTS = [
    (demo_id(7, 1), demo_id(4, 1), demo_id(6, 1), 12, None, False, "ערכת לייזר לכל תחנה"),
    (demo_id(7, 2), demo_id(4, 1), demo_id(6, 2), 12, None, False, "מטען לכל ערכה"),
    (demo_id(7, 3), demo_id(4, 1), demo_id(6, 3), 6, None, False, "סטים לגיבוי"),
    (demo_id(7, 4), demo_id(4, 1), demo_id(6, 12), 1, None, True, "להסברים ולפתיחה"),
    (demo_id(7, 5), demo_id(4, 3), demo_id(6, 4), 10, None, False, "שלט לכל קבוצה"),
    (demo_id(7, 6), demo_id(4, 3), demo_id(6, 5), 4, None, False, "כרטיסי שאלות לפי סבבים"),
    (demo_id(7, 7), demo_id(4, 3), demo_id(6, 12), 1, None, True, "להנחיית החידון"),
    (demo_id(7, 8), demo_id(4, 4), demo_id(6, 6), 0, Decimal("1.0"), False, "תיק לכל משתתף"),
    (demo_id(7, 9), demo_id(4, 4), demo_id(6, 7), 10, None, False, "קופסאות טושים לעמדות"),
    (demo_id(7, 10), demo_id(4, 4), demo_id(6, 8), 8, None, False, "שבלונות משותפות"),
    (demo_id(7, 11), demo_id(4, 2), demo_id(6, 9), 50, None, False, "מעטפות משימה לתחנות"),
    (demo_id(7, 12), demo_id(4, 2), demo_id(6, 10), 50, None, False, "כרטיסי צופן"),
    (demo_id(7, 13), demo_id(4, 5), demo_id(6, 11), 0, Decimal("1.0"), False, "קנבס אישי לכל משתתף"),
    (demo_id(7, 14), demo_id(4, 5), demo_id(6, 7), 12, None, False, "טושים לקישוט"),
]


BOOKINGS = [
    (demo_id(8, 1), demo_id(1, 1), demo_id(2, 1), "פעילות פתיחת שנה - בית ספר נועם ירושלים", "2026-09-01 08:30:00+03", "אולם ספורט נועם", "רחוב הדמו 1", "ירושלים", 72, "כיתות ה-ו", BookingStatus.CONFIRMED.value, "להגיע שעה לפני לפתיחת תחנות. נתוני דמו.", "יש להיערך לחלוקה ל-6 קבוצות.", True, "נדרש רכב להובלת ערכות לייזר", "להעמיס ערכות לייזר, מטענים ורמקול בערב קודם."),
    (demo_id(8, 2), demo_id(1, 4), demo_id(2, 5), "יום שיא חסד - אולפנת אורות", "2026-09-14 10:00:00+03", "אולפנת אורות", "רחוב האור 18", "בית שמש", 95, "כיתות ט-י", BookingStatus.NEW.value, "לשלב תחנות חשיבה וחידון. נתוני דמו.", "נא להכין מקרן אם יש.", False, None, "להביא שלטים וכרטיסי צופן."),
    (demo_id(8, 3), demo_id(1, 2), demo_id(2, 3), 'פעילות חנוכה - מתנ"ס גבעת שמואל', "2026-12-10 17:00:00+02", 'מתנ"ס גבעת שמואל', "שדרות הקהילה 12", "גבעת שמואל", 80, "משפחות", BookingStatus.NEW.value, "סדנת יצירה עם אפשרות לשני סבבים. נתוני דמו.", "נדרש שולחן לכל 10 משתתפים.", True, "רכב קטן לחומרי יצירה", "להעמיס תיקי בד, טושים ושבלונות."),
    (demo_id(8, 4), demo_id(1, 6), demo_id(2, 7), "קייטנת קיץ - בית שמש", "2026-08-05 09:00:00+03", "פארק העיר", "פארק העיר 3", "בית שמש", 100, "ילדי קייטנה", BookingStatus.NEW.value, "פעילות סוכות מוקדמת לדוגמה עבור בדיקות עומס. נתוני דמו.", "לוודא אזור מוצל.", True, "נדרש רכב לחומרי יצירה", "להביא קנבסים, טושים וכבלים מאריכים."),
    (demo_id(8, 5), demo_id(1, 3), demo_id(2, 4), "ערב משפחות - עיריית מודיעין", "2026-10-20 18:30:00+03", "היכל התרבות מודיעין", "כיכר העיר 5", "מודיעין", 140, "משפחות", BookingStatus.CONFIRMED.value, "אירוע משפחות גדול עם שתי מדריכות. נתוני דמו.", "פתיחת שערים בשעה 18:00.", True, "רכב גדול לציוד כללי", "להעמיס ארגז כללי, רמקול וקנבסים."),
]


BOOKING_ACTIVITIES = [
    (demo_id(9, 1), demo_id(8, 1), demo_id(4, 1), "2026-09-01 09:00:00+03", 90, 72, "אולם ספורט", 1, "חלוקה ל-6 קבוצות"),
    (demo_id(9, 2), demo_id(8, 2), demo_id(4, 3), "2026-09-14 10:00:00+03", 60, 95, "אודיטוריום", 1, "חידון פתיחה"),
    (demo_id(9, 3), demo_id(8, 2), demo_id(4, 2), "2026-09-14 11:15:00+03", 75, 95, "חצר מרכזית", 2, "תחנות צופן"),
    (demo_id(9, 4), demo_id(8, 3), demo_id(4, 4), "2026-12-10 17:00:00+02", 80, 80, "חדר יצירה", 1, "סדנה משפחתית"),
    (demo_id(9, 5), demo_id(8, 4), demo_id(4, 5), "2026-08-05 09:30:00+03", 70, 100, "מתחם מוצל", 1, "סבב קייטנה"),
    (demo_id(9, 6), demo_id(8, 5), demo_id(4, 5), "2026-10-20 18:45:00+03", 70, 140, "אולם כניסה", 1, "עמדות משפחתיות"),
]


BOOKING_INSTRUCTORS = [
    (demo_id(10, 1), demo_id(9, 1), demo_id(3, 1), "מדריכה ראשית"),
    (demo_id(10, 2), demo_id(9, 1), demo_id(3, 6), "אחראית ציוד"),
    (demo_id(10, 3), demo_id(9, 2), demo_id(3, 3), "מנחת חידון"),
    (demo_id(10, 4), demo_id(9, 3), demo_id(3, 4), "מנחת תחנות"),
    (demo_id(10, 5), demo_id(9, 4), demo_id(3, 2), "מדריכת סדנה"),
    (demo_id(10, 6), demo_id(9, 5), demo_id(3, 5), "מדריכת יצירה"),
    (demo_id(10, 7), demo_id(9, 6), demo_id(3, 2), "מדריכת סדנה"),
    (demo_id(10, 8), demo_id(9, 6), demo_id(3, 5), "מדריכה נוספת"),
]


BOOKING_EQUIPMENT = [
    (demo_id(11, 1), demo_id(8, 1), demo_id(6, 1), 12, "מתוכנן", "12 ערכות לייזר"),
    (demo_id(11, 2), demo_id(8, 1), demo_id(6, 2), 12, "מתוכנן", "12 מטענים"),
    (demo_id(11, 3), demo_id(8, 1), demo_id(6, 3), 6, "מתוכנן", "סוללות גיבוי"),
    (demo_id(11, 4), demo_id(8, 1), demo_id(6, 12), 1, "מתוכנן", "רמקול נייד"),
    (demo_id(11, 5), demo_id(8, 2), demo_id(6, 4), 10, "מתוכנן", "שלטי חידון"),
    (demo_id(11, 6), demo_id(8, 2), demo_id(6, 5), 5, "מתוכנן", "כרטיסי שאלות"),
    (demo_id(11, 7), demo_id(8, 2), demo_id(6, 9), 50, "מתוכנן", "מעטפות משימה"),
    (demo_id(11, 8), demo_id(8, 2), demo_id(6, 10), 50, "מתוכנן", "כרטיסי צופן"),
    (demo_id(11, 9), demo_id(8, 3), demo_id(6, 6), 80, "מתוכנן", "80 תיקי בד"),
    (demo_id(11, 10), demo_id(8, 3), demo_id(6, 7), 12, "מתוכנן", "טושים לבד"),
    (demo_id(11, 11), demo_id(8, 3), demo_id(6, 8), 8, "מתוכנן", "שבלונות עיצוב"),
    (demo_id(11, 12), demo_id(8, 4), demo_id(6, 11), 100, "מתוכנן", "100 קנבסים"),
    (demo_id(11, 13), demo_id(8, 4), demo_id(6, 13), 3, "מתוכנן", "כבלים מאריכים"),
    (demo_id(11, 14), demo_id(8, 5), demo_id(6, 11), 140, "מתוכנן", "קנבסים למשפחות"),
    (demo_id(11, 15), demo_id(8, 5), demo_id(6, 14), 2, "מתוכנן", "ארגז ציוד כללי"),
]


PRICE_COMPONENTS = [
    (demo_id(12, 1), demo_id(8, 1), "פעילות", "פעילות תפוס את האור", 1, 1800, 1800, 1),
    (demo_id(12, 2), demo_id(8, 1), "תוספת", "תוספת נסיעות והובלה", 1, 250, 250, 2),
    (demo_id(12, 3), demo_id(8, 2), "פעילות", "חידון שלטים", 1, 900, 900, 1),
    (demo_id(12, 4), demo_id(8, 2), "פעילות", "מירוץ הצופן", 1, 1500, 1500, 2),
    (demo_id(12, 5), demo_id(8, 2), "הנחה", "הנחת כמות", 1, -300, -300, 3),
    (demo_id(12, 6), demo_id(8, 3), "פעילות", "סדנת תיק בעיצוב אישי", 80, 34, 2720, 1),
    (demo_id(12, 7), demo_id(8, 3), "תוספת", "תוספת נסיעות והובלה", 1, 250, 250, 2),
    (demo_id(12, 8), demo_id(8, 4), "פעילות", "קישוט סוכה על קנבס", 100, 34, 3400, 1),
    (demo_id(12, 9), demo_id(8, 5), "פעילות", "קישוט סוכה על קנבס", 140, 28, 3920, 1),
    (demo_id(12, 10), demo_id(8, 5), "תוספת", "תוספת נסיעות והובלה", 1, 350, 350, 2),
]


def booking_seed_rows() -> list[tuple]:
    first_activity_by_booking: dict[str, str] = {}
    for activity_row in BOOKING_ACTIVITIES:
        booking_id = activity_row[1]
        activity_id = activity_row[2]
        first_activity_by_booking.setdefault(booking_id, activity_id)

    booking_activity_ids_with_instructors = {row[1] for row in BOOKING_INSTRUCTORS}
    bookings_with_instructors = {
        activity_row[1]
        for activity_row in BOOKING_ACTIVITIES
        if activity_row[0] in booking_activity_ids_with_instructors
    }

    agreed_prices: dict[str, Decimal] = {}
    for price_component in PRICE_COMPONENTS:
        booking_id = price_component[1]
        total_price = price_component[6]
        agreed_prices[booking_id] = agreed_prices.get(booking_id, Decimal("0")) + Decimal(total_price)

    rows = []
    for booking in BOOKINGS:
        (
            booking_id,
            _customer_id,
            _primary_contact_id,
            _event_title,
            event_date,
            location_name,
            _location_address,
            _city,
            participants_count,
            _audience_type,
            _status,
            internal_notes,
            *_remaining,
        ) = booking
        rows.append(
            (
                *booking,
                first_activity_by_booking[booking_id],
                event_date,
                location_name,
                participants_count,
                agreed_prices.get(booking_id, Decimal("0")),
                booking_id in bookings_with_instructors,
                internal_notes,
                1,
            )
        )
    return rows


EXTERNAL_REFERENCE_CHECKS = [
    ("customer_contacts", "customer_id -> customers.id", "SELECT COUNT(*) FROM customer_contacts WHERE customer_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("users", "customer_id -> customers.id", "SELECT COUNT(*) FROM users WHERE customer_id::text = ANY(%s) AND NOT (email = ANY(%s));"),
    ("users", "instructor_id -> instructors.id", "SELECT COUNT(*) FROM users WHERE instructor_id::text = ANY(%s) AND NOT (email = ANY(%s));"),
    ("bookings", "customer_id -> customers.id", "SELECT COUNT(*) FROM bookings WHERE customer_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("bookings", "primary_contact_id -> customer_contacts.id", "SELECT COUNT(*) FROM bookings WHERE primary_contact_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("bookings", "activity_id -> activities.id", "SELECT COUNT(*) FROM bookings WHERE activity_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("activity_instruction_notes", "activity_id -> activities.id", "SELECT COUNT(*) FROM activity_instruction_notes WHERE activity_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("activity_images", "activity_id -> activities.id", "SELECT COUNT(*) FROM activity_images WHERE activity_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("activity_equipment_requirements", "activity_id -> activities.id", "SELECT COUNT(*) FROM activity_equipment_requirements WHERE activity_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("activity_equipment_requirements", "inventory_item_id -> inventory_items.id", "SELECT COUNT(*) FROM activity_equipment_requirements WHERE inventory_item_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("booking_activities", "booking_id -> bookings.id", "SELECT COUNT(*) FROM booking_activities WHERE booking_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("booking_activities", "activity_id -> activities.id", "SELECT COUNT(*) FROM booking_activities WHERE activity_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("booking_instructors", "booking_activity_id -> booking_activities.id", "SELECT COUNT(*) FROM booking_instructors WHERE booking_activity_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("booking_instructors", "instructor_id -> instructors.id", "SELECT COUNT(*) FROM booking_instructors WHERE instructor_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("booking_equipment_items", "booking_id -> bookings.id", "SELECT COUNT(*) FROM booking_equipment_items WHERE booking_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("booking_equipment_items", "inventory_item_id -> inventory_items.id", "SELECT COUNT(*) FROM booking_equipment_items WHERE inventory_item_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("booking_price_components", "booking_id -> bookings.id", "SELECT COUNT(*) FROM booking_price_components WHERE booking_id::text = ANY(%s) AND NOT (id::text = ANY(%s));"),
    ("booking_events", "aggregate_id -> demo booking aggregate", "SELECT COUNT(*) FROM booking_events WHERE aggregate_id::text = ANY(%s) AND NOT (event_id::text = ANY(%s));"),
    ("booking_events", "actor_user_id -> reserved demo user", "SELECT COUNT(*) FROM booking_events be JOIN users u ON u.id = be.actor_user_id WHERE u.email = ANY(%s) AND NOT (be.aggregate_id::text = ANY(%s));"),
]


DELETION_TABLES = [
    "booking_price_components",
    "booking_equipment_items",
    "booking_instructors",
    "booking_activities",
    "booking_events",
    "bookings",
    "activity_equipment_requirements",
    "activity_images",
    "inventory_items",
    "activity_instruction_notes",
    "activities",
    "users",
    "instructors",
    "customer_contacts",
    "customers",
]


def check_external_references(conn: Connection) -> list[ExternalReference]:
    reserved_ids = demo_ids()
    references: list[ExternalReference] = []
    with conn.cursor() as cur:
        for table, relationship, query in EXTERNAL_REFERENCE_CHECKS:
            if table == "users":
                params = (reserved_ids, list(DEMO_USER_EMAILS))
            elif table == "booking_events" and relationship.startswith("actor_user_id"):
                params = (list(DEMO_USER_EMAILS), reserved_ids)
            else:
                params = (reserved_ids, reserved_ids)
            cur.execute(query, params)
            count = int(cur.fetchone()[0])
            if count:
                references.append(ExternalReference(table, relationship, count))
    return references


def inspect_demo_records(conn: Connection) -> dict[str, int]:
    reserved_ids = demo_ids()
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        for table in DELETION_TABLES:
            if table == "booking_events":
                cur.execute("SELECT COUNT(*) FROM booking_events WHERE aggregate_id::text = ANY(%s);", (reserved_ids,))
            elif table == "activity_images":
                cur.execute("SELECT COUNT(*) FROM activity_images WHERE activity_id::text = ANY(%s);", (reserved_ids,))
            elif table == "users":
                cur.execute("SELECT COUNT(*) FROM users WHERE email = ANY(%s);", (list(DEMO_USER_EMAILS),))
            else:
                cur.execute(f"SELECT COUNT(*) FROM {table} WHERE id::text = ANY(%s);", (reserved_ids,))
            counts[table] = int(cur.fetchone()[0])
    return counts


def delete_demo_data(conn: Connection) -> None:
    demo_id_list = demo_ids()
    with conn.cursor() as cur:
        for table in DELETION_TABLES:
            if table == "booking_events":
                cur.execute("DELETE FROM booking_events WHERE aggregate_id::text = ANY(%s);", (demo_id_list,))
            elif table == "activity_images":
                cur.execute("DELETE FROM activity_images WHERE activity_id::text = ANY(%s);", (demo_id_list,))
            elif table == "users":
                cur.execute("DELETE FROM users WHERE email = ANY(%s);", (list(DEMO_USER_EMAILS),))
            else:
                cur.execute(f"DELETE FROM {table} WHERE id::text = ANY(%s);", (demo_id_list,))


def insert_demo_business_data(conn: Connection) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO customers (
                id, name, customer_type, city, address, phone, email, notes
            )
            VALUES (
                %(id)s, %(name)s, %(customer_type)s, %(city)s, %(address)s,
                %(phone)s, %(email)s, %(notes)s
            );
            """,
            CUSTOMERS,
        )
        cur.executemany(
            """
            INSERT INTO customer_contacts (
                id, customer_id, full_name, role_title, phone, email, is_primary, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            [(*contact, DEMO_MARKER) for contact in CONTACTS],
        )
        cur.executemany(
            """
            INSERT INTO instructors (id, full_name, phone, email, city, notes)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            [(row[0], row[1], row[2], row[3], row[4], f"{DEMO_MARKER}. {row[5]}") for row in INSTRUCTORS],
        )
        cur.executemany(
            """
            INSERT INTO activities (
                id, name, description, default_duration_minutes, min_participants,
                max_participants, base_price, price_notes, default_setup_minutes,
                default_cleanup_minutes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            ACTIVITIES,
        )
        cur.executemany(
            """
            INSERT INTO activity_instruction_notes (
                id, activity_id, title, body, sort_order
            )
            VALUES (%s, %s, %s, %s, %s);
            """,
            INSTRUCTION_NOTES,
        )
        cur.executemany(
            """
            INSERT INTO inventory_items (
                id, name, category, unit, quantity_total, quantity_available,
                storage_location, needs_charging, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            [(*item, DEMO_MARKER) for item in INVENTORY_ITEMS],
        )
        cur.executemany(
            """
            INSERT INTO activity_equipment_requirements (
                id, activity_id, inventory_item_id, quantity_required,
                quantity_per_participant, is_optional, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            ACTIVITY_REQUIREMENTS,
        )
        cur.executemany(
            """
            INSERT INTO bookings (
                id, customer_id, primary_contact_id, event_title, event_date,
                location_name, location_address, city, participants_count,
                audience_type, status, internal_notes, customer_notes,
                requires_vehicle, vehicle_notes, loading_notes,
                activity_id, event_at, venue, participant_count, agreed_price,
                requires_instructor, notes, version
            )
            VALUES (
                %s, %s, %s, %s, %s::timestamptz, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s::timestamptz, %s, %s, %s, %s, %s, %s
            );
            """,
            booking_seed_rows(),
        )
        cur.executemany(
            """
            INSERT INTO booking_activities (
                id, booking_id, activity_id, start_time, duration_minutes,
                participants_count, location_detail, sort_order, notes
            )
            VALUES (%s, %s, %s, %s::timestamptz, %s, %s, %s, %s, %s);
            """,
            BOOKING_ACTIVITIES,
        )
        cur.executemany(
            """
            INSERT INTO booking_instructors (
                id, booking_activity_id, instructor_id, role, notes
            )
            VALUES (%s, %s, %s, %s, %s);
            """,
            [(*row, DEMO_MARKER) for row in BOOKING_INSTRUCTORS],
        )
        cur.executemany(
            """
            INSERT INTO booking_equipment_items (
                id, booking_id, inventory_item_id, quantity_planned, status, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            BOOKING_EQUIPMENT,
        )
        cur.executemany(
            """
            INSERT INTO booking_price_components (
                id, booking_id, component_type, description, quantity,
                unit_price, total_price, sort_order
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            PRICE_COMPONENTS,
        )
    return {
        "Customers": len(CUSTOMERS),
        "Contacts": len(CONTACTS),
        "Instructors": len(INSTRUCTORS),
        "Activities": len(ACTIVITIES),
        "Instruction notes": len(INSTRUCTION_NOTES),
        "Inventory items": len(INVENTORY_ITEMS),
        "Activity equipment requirements": len(ACTIVITY_REQUIREMENTS),
        "Bookings": len(BOOKINGS),
        "Booking activities": len(BOOKING_ACTIVITIES),
        "Booking instructors": len(BOOKING_INSTRUCTORS),
        "Booking equipment items": len(BOOKING_EQUIPMENT),
        "Booking price components": len(PRICE_COMPONENTS),
    }


def seed_demo_data(conn: Connection, *, dry_run: bool = False) -> dict[str, object]:
    references = check_external_references(conn)
    if references:
        raise DemoSeedSafetyError(references)

    existing_counts = inspect_demo_records(conn)
    recreated_counts = {
        "Customers": len(CUSTOMERS),
        "Contacts": len(CONTACTS),
        "Instructors": len(INSTRUCTORS),
        "Activities": len(ACTIVITIES),
        "Instruction notes": len(INSTRUCTION_NOTES),
        "Inventory items": len(INVENTORY_ITEMS),
        "Activity equipment requirements": len(ACTIVITY_REQUIREMENTS),
        "Bookings": len(BOOKINGS),
        "Booking activities": len(BOOKING_ACTIVITIES),
        "Booking instructors": len(BOOKING_INSTRUCTORS),
        "Booking equipment items": len(BOOKING_EQUIPMENT),
        "Booking price components": len(PRICE_COMPONENTS),
        "Demo users": len(DEMO_USER_EMAILS),
    }
    report: dict[str, object] = {
        "mode": "dry-run" if dry_run else "refresh",
        "delete_counts": existing_counts,
        "recreate_counts": recreated_counts,
    }
    if dry_run:
        conn.rollback()
        return report

    try:
        delete_demo_data(conn)
        insert_demo_business_data(conn)
        seed_demo_users(conn, commit=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return report


def _print_report(report: dict[str, object]) -> None:
    print(f"Demo data {report['mode']} completed safely.")
    print("Rows by object group that would be deleted:" if report["mode"] == "dry-run" else "Rows deleted by object group:")
    for table, count in report["delete_counts"].items():
        print(f"  {table}: {count}")
    print("Rows and object groups that would be recreated:" if report["mode"] == "dry-run" else "Rows recreated by object group:")
    for label, count in report["recreate_counts"].items():
        print(f"  {label}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely refresh the deterministic demo dataset.")
    parser.add_argument("--dry-run", action="store_true", help="Run safety checks and preview changes without writing.")
    args = parser.parse_args()
    with get_connection() as conn:
        report = seed_demo_data(conn, dry_run=args.dry_run)
    _print_report(report)


if __name__ == "__main__":
    main()
