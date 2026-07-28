from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from backend.app.domain.bookings.status import BookingStatus


BUSINESS_TIMEZONE = ZoneInfo("Asia/Jerusalem")
DEMO_MARKER = "נתוני דמו - חוויה עם נשמה"
CUSTOMER_LOGIN_EMAIL = "customer@example.com"
INSTRUCTOR_LOGIN_EMAIL = "instructor@example.com"
MANAGER_LOGIN_EMAIL = "manager@example.com"
PRIMARY_CONTACT_BY_CUSTOMER_KEY = {
    "customer-1": "contact-1",
    "customer-2": "contact-3",
    "customer-3": "contact-5",
    "customer-4": "contact-7",
    "customer-5": "contact-8",
    "customer-6": "contact-9",
    "customer-7": "contact-10",
    "customer-8": "contact-11",
    "customer-9": "contact-12",
    "customer-10": "contact-13",
    "customer-11": "contact-14",
    "customer-12": "contact-15",
    "customer-13": "contact-16",
    "customer-14": "contact-17",
    "customer-15": "contact-18",
    "customer-16": "contact-19",
}


def demo_id(group: int, number: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{group:04d}{number:08d}")


@dataclass(frozen=True)
class CustomerSeed:
    key: str
    id: UUID
    name: str
    customer_type: str
    city: str
    address: str
    phone: str
    email: str
    notes: str


@dataclass(frozen=True)
class ContactSeed:
    key: str
    id: UUID
    customer_key: str
    full_name: str
    role_title: str
    phone: str
    email: str
    is_primary: bool = False


@dataclass(frozen=True)
class InstructorSeed:
    key: str
    id: UUID
    full_name: str
    phone: str
    email: str
    city: str
    notes: str


@dataclass(frozen=True)
class ActivitySeed:
    key: str
    id: UUID
    name: str
    description: str
    target_audience: str
    duration_minutes: int
    min_participants: int
    max_participants: int
    recommended_capacity: int
    base_price: Decimal
    price_notes: str
    pricing_rule: str
    required_equipment: str
    preparation_notes: str
    season: str
    tags: str
    setup_minutes: int
    cleanup_minutes: int


@dataclass(frozen=True)
class InventorySeed:
    key: str
    id: UUID
    name: str
    category: str
    unit: str
    quantity_total: int
    quantity_available: int
    storage_location: str
    needs_charging: bool = False


@dataclass(frozen=True)
class InstructionSeed:
    id: UUID
    activity_key: str
    title: str
    body: str
    sort_order: int


@dataclass(frozen=True)
class RequirementSeed:
    id: UUID
    activity_key: str
    inventory_key: str
    quantity_required: int
    quantity_per_participant: Decimal | None
    is_optional: bool
    notes: str


@dataclass(frozen=True)
class BookingActivitySeed:
    id: UUID
    activity_key: str
    offset_minutes: int
    duration_minutes: int
    participants_count: int
    location_detail: str
    sort_order: int
    notes: str
    assignment_required: bool = True


@dataclass(frozen=True)
class AssignmentStep:
    booking_activity_id: UUID
    instructor_key: str
    action: str


@dataclass(frozen=True)
class EquipmentUseSeed:
    id: UUID
    inventory_key: str
    quantity: int
    status: str
    notes: str


@dataclass(frozen=True)
class PriceComponentSeed:
    id: UUID
    component_type: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    sort_order: int


@dataclass(frozen=True)
class BookingSeed:
    key: str
    id: UUID
    customer_key: str
    contact_key: str
    title: str
    days_from_now: int
    hour: int
    city: str
    venue: str
    address: str
    participants: int
    audience_type: str
    status: str
    requires_instructor: bool
    assignment_state: Literal["assigned", "unassigned", "not_required"]
    internal_notes: str
    customer_notes: str
    requires_vehicle: bool
    vehicle_notes: str | None
    loading_notes: str | None
    activities: tuple[BookingActivitySeed, ...]
    assignments: tuple[AssignmentStep, ...] = field(default_factory=tuple)
    equipment: tuple[EquipmentUseSeed, ...] = field(default_factory=tuple)
    prices: tuple[PriceComponentSeed, ...] = field(default_factory=tuple)
    include_sign_quiz_addon: bool = False

    @property
    def event_at(self) -> datetime:
        base = datetime.now(BUSINESS_TIMEZONE).replace(minute=0, second=0, microsecond=0)
        return base + timedelta(days=self.days_from_now, hours=self.hour - base.hour)

    @property
    def agreed_price(self) -> Decimal:
        return sum((item.total_price for item in self.prices), Decimal("0"))


CUSTOMERS = tuple(
    CustomerSeed(f"customer-{i}", demo_id(1, i), name, ctype, city, address, phone, email, f"{DEMO_MARKER}. {notes}")
    for i, (name, ctype, city, address, phone, email, notes) in enumerate(
        [
            ("בית ספר נועם ירושלים", "בית ספר", "ירושלים", "רחוב הדמו 1", "02-5000001", "noam-demo@example.com", "בית ספר יסודי לאירועי שיא."),
            ('מתנ"ס גבעת שמואל', 'מתנ"ס', "גבעת שמואל", "שדרות הקהילה 12", "03-5000002", "matnas-gs-demo@example.com", "מרכז קהילתי לילדים ומשפחות."),
            ("עיריית מודיעין - אגף תרבות תורנית", "עירייה", "מודיעין", "כיכר העיר 5", "08-5000003", "modiin-demo@example.com", "אירועים קהילתיים רחבי היקף."),
            ("אולפנת אורות", "אולפנה", "בית שמש", "רחוב האור 18", "02-5000004", "orot-demo@example.com", "ימי גיבוש וחסד לתלמידות."),
            ("תלמוד תורה דרכי אבות", "תלמוד תורה", "פתח תקווה", "רחוב האבות 22", "03-5000005", "darchei-avot-demo@example.com", "פעילות ערכית לכיתות ד-ח."),
            ("קהילת בית מורשת", "קהילה", "אפרת", "רחוב הזית 9", "02-5000006", "beit-moreshet-demo@example.com", "אירועים למשפחות ולקהילה."),
            ("מרכז משפחות רקפת", "מרכז משפחות", "רחובות", "רחוב המדע 14", "08-5000007", "rakefet-demo@example.com", "סדנאות הורים וילדים."),
            ("קייטנת קיץ שמחה", "קייטנה", "בית שמש", "פארק העיר 3", "02-5000008", "kaytana-demo@example.com", "קייטנת קיץ רב גילאית."),
            ("בית ספר אמונה אשדוד", "בית ספר", "אשדוד", "רחוב הנמל 31", "08-5000009", "emuna-ashdod-demo@example.com", "פעילויות חג ומורשת."),
            ("אולפנת הדר רעננה", "אולפנה", "רעננה", "רחוב הפרחים 7", "09-5000010", "hadar-demo@example.com", "פעילות חברתית לתלמידות תיכון."),
            ("מרכז קהילתי כרמיאל", "מרכז קהילתי", "כרמיאל", "שדרות הגליל 20", "04-5000011", "karmiel-demo@example.com", "אירועים קהילתיים למשפחות."),
            ('מתנ"ס גבעתיים', 'מתנ"ס', "גבעתיים", "רחוב כצנלסון 41", "03-5000012", "givatayim-demo@example.com", "חוגים ואירועי חגים."),
            ("בית ספר מעלות התורה", "בית ספר", "מעלה אדומים", "רחוב הרכס 4", "02-5000013", "maalot-demo@example.com", "פעילויות שכבתיות."),
            ("קהילת נווה שמחה", "קהילה", "ירושלים", "רחוב הנביאים 50", "02-5000014", "neve-simcha-demo@example.com", "פעילות משפחות בשבתות וחגים."),
            ("מרכז נוער איתן", "מרכז נוער", "מודיעין", "רחוב עמק האלה 6", "08-5000015", "eitan-demo@example.com", "פעילות נוער ואתגר."),
            ("קייטנת בין הזמנים", "קייטנה", "פתח תקווה", "רחוב התקווה 10", "03-5000016", "bein-hazmanim-demo@example.com", "קייטנה עירונית לחופשות."),
        ],
        start=1,
    )
)


CONTACTS = tuple(
    ContactSeed(f"contact-{i}", demo_id(2, i), f"customer-{customer}", name, role, phone, f"contact{i}@example.com", primary)
    for i, (customer, name, role, phone, primary) in enumerate(
        [
            (1, "רבקה לוי", "רכזת חברתית", "050-6000001", True), (1, "אליהו כהן", "מנהל", "052-6000002", False),
            (2, "נעמה ישראלי", "רכזת תרבות", "054-6000003", True), (2, "אורית שמש", "מזכירה", "050-6000004", False),
            (3, "יוסי בן דוד", "רכז תרבות", "052-6000005", True), (3, "תהילה שטרן", "מנהלת קהילה", "054-6000006", False),
            (4, "אפרת מזרחי", "רכזת שכבה", "050-6000007", True), (5, "שמואל פרידמן", "מנהל תלמוד תורה", "052-6000008", True),
            (6, "חנה אברהם", "מנהלת קהילה", "054-6000009", True), (7, "דבורה מלכה", "רכזת משפחות", "050-6000010", True),
            (8, "חני כהן", "מנהלת קייטנה", "052-6000011", True), (9, "שירה וקנין", "רכזת חברתית", "054-6000012", True),
            (10, "רחל גולד", "רכזת שכבה", "050-6000013", True), (11, "מרים ביטון", "רכזת תרבות", "052-6000014", True),
            (12, "יעקב דיין", "מנהל", "054-6000015", True), (13, "לאה צור", "רכזת חברתית", "050-6000016", True),
            (14, "אביגיל רוזן", "מנהלת קהילה", "052-6000017", True), (15, "איתמר שלו", "רכז נוער", "054-6000018", True),
            (16, "שרה לוין", "מנהלת קייטנה", "050-6000019", True), (10, "נעמי לביא", "מזכירה", "052-6000020", False),
            (11, "אביחי כהן", "רכז חברתי", "054-6000021", False), (13, "טליה מור", "רכזת שכבה", "050-6000022", False),
            (14, "יהודה סלע", "גבאי קהילה", "052-6000023", False), (15, "הילה ארז", "מזכירה", "054-6000024", False),
        ],
        start=1,
    )
)


INSTRUCTORS = tuple(
    InstructorSeed(f"instructor-{i}", demo_id(3, i), name, phone, f"instructor{i}@example.com", city, f"{DEMO_MARKER}. {notes}")
    for i, (name, phone, city, notes) in enumerate(
        [
            ("מיכל כהן", "050-7000001", "ירושלים", "מדריכה ותיקה לפעילויות אור ותחנות."),
            ("שירה לוי", "052-7000002", "בית שמש", "מתמחה בסדנאות יצירה וחגים."),
            ("תמר ישראלי", "054-7000003", "מודיעין", "מובילת חידונים ומשחקי קבוצה."),
            ("הדס אברהם", "050-7000004", "גבעת שמואל", "אחראית אירועי משפחות גדולים."),
            ("יעל מזרחי", "052-7000005", "רעננה", "מדריכת סדנאות לבנות מצווה."),
            ("נועה שפירא", "054-7000006", "פתח תקווה", "אחראית ציוד והפעלה בשטח."),
            ("רחלי סבג", "050-7000007", "אשדוד", "מדריכת יצירה לגיל הרך וליסודי."),
            ("מוריה דיין", "052-7000008", "רחובות", "מנחת קבוצות ומשפחות."),
            ("אורטל פרץ", "054-7000009", "כרמיאל", "מדריכה לאירועים קהילתיים בצפון."),
            ("בת שבע רוזן", "050-7000010", "אפרת", "מובילת פעילויות מורשת."),
            ("נעמה ברק", "052-7000011", "גבעתיים", "מדריכת מרוצי צופן ותחנות."),
        ],
        start=1,
    )
)


ACTIVITIES = tuple(
    ActivitySeed(f"activity-{i}", demo_id(4, i), name, desc, audience, duration, minp, maxp, cap, Decimal(str(price)), notes, rule, equipment, prep, season, tags, setup, cleanup)
    for i, (name, desc, audience, duration, minp, maxp, cap, price, notes, rule, equipment, prep, season, tags, setup, cleanup) in enumerate(
        [
            ("תפוס את האור", "פעילות אתגרית עם יחידות אור צבעוניות, משימות קבוצתיות וניקוד.", "כיתות ד-ח", 90, 20, 120, 80, 1200, 'מחיר דמו לצורך בדיקת המערכת בלבד.', "מחיר בסיס עד 60 משתתפים ותוספת למשתתף נוסף.", "יחידות אור צבעוניות, מטענים, סוללות נטענות, רמקול נייד", "לטעון ציוד ערב קודם ולבדוק סוללות.", "כל השנה", "אתגר,קבוצות,אור", 45, 30),
            ("מירוץ הצופן", "משחק תחנות לפענוח כתבי חידה וצפנים.", "נוער ובתי ספר", 75, 25, 100, 80, 1500, 'מחיר דמו לצורך בדיקת המערכת בלבד.', "מחיר למפגש כולל מעטפות ומשימות.", "מעטפות משימה, כרטיסי צופן, שלטי חידון", "להכין מעטפות לפי מספר קבוצות.", "כל השנה", "צופן,תחנות,נוער", 35, 25),
            ("חידון שלטים", "חידון קבוצתי עם שאלות ידע, זריזות ושיתוף פעולה.", "כיתות ומשפחות", 60, 15, 90, 70, 900, 'מחיר דמו לצורך בדיקת המערכת בלבד.', "מחיר למפגש; תוספת כאפשרות לפעילות סוכה.", "שלטי חידון, כרטיסי שאלות, רמקול נייד", "לבדוק מקרן והגברה.", "כל השנה", "חידון,ידע", 25, 20),
            ("סדנת תיק בעיצוב אישי", "סדנת יצירה שבה כל משתתף מעצב תיק אישי.", "ילדים ונוער", 80, 20, 120, 90, 1200, 'מחיר דמו לצורך בדיקת המערכת בלבד.', "מחיר לפי משתתף עם מינימום הזמנה.", "תיקי בד, חומרי הדפסה, טושים", "לספור חומרי יצירה לפי משתתפים.", "כל השנה", "יצירה,סדנה", 40, 30),
            ("קישוט סוכה בעיצוב אישי על קנבס", "סדנת יצירה לחג הסוכות על קנבס אישי.", "בתי ספר וקהילות", 45, 20, 150, 100, 3400, 'עד 100 ילדים: 34 ₪ למשתתף כולל מע״מ; מעל 100 ילדים: 28 ₪ למשתתף כולל מע״מ; תוספת חידון שלטים: 10 ₪ למשתתף.', "מחיר רשמי לפי מדרגות משתתפים.", "קנבסים, טושים, שולחנות מתקפלים", "לוודא מספר שולחנות מתאים.", "סוכות", "סוכות,יצירה,קנבס", 35, 25),
            ("אירוע משפחות - בעקבות המורשת", "אירוע קהילתי רב תחנות למשפחות סביב מורשת וחיבור בין דורות.", "משפחות וקהילות", 120, 80, 300, 180, 2800, 'מחיר דמו לצורך בדיקת המערכת בלבד.', "מחיר בסיס לאירוע משפחות ותוספת תחנות לפי היקף.", "רמקול נייד, ארגזי ציוד, שלטי חידון", "לתאם שטח מוצל ונגישות לרכב ציוד.", "כל השנה", "משפחות,מורשת,קהילה", 60, 40),
            ("סדנת חנוכייה בעיצוב אישי", "סדנת יצירה לחנוכה עם בסיסי חנוכייה וחומרי קישוט.", "ילדים ומשפחות", 75, 20, 120, 80, 1600, 'מחיר דמו לצורך בדיקת המערכת בלבד.', "מחיר לפי משתתף וחומרי יצירה.", "בסיסי חנוכייה, חומרי הדפסה, שולחנות", "להכין ערכות גיבוי.", "חנוכה", "חנוכה,יצירה", 40, 30),
            ("סדנת הפקת שמן זית", "הדגמה חווייתית של מסיק, כתישה והפקת שמן זית.", "כיתות ומשפחות", 70, 25, 100, 80, 1800, 'מחיר דמו לצורך בדיקת המערכת בלבד.', "מחיר למפגש כולל ערכת הדגמה.", "ארגזי ציוד, שולחנות מתקפלים", "להגיע מוקדם להקמה ולבדוק מים קרובים.", "חנוכה", "שמן,מורשת,חנוכה", 45, 30),
            ("מתחם תחנות חווייתי", "מתחם תחנות גדול לאירועים עם כמה מוקדי פעילות במקביל.", "אירועים גדולים", 150, 70, 250, 150, 3500, 'כ-70 ילדים: 3,500 ₪; כ-150 ילדים: 4,000 ₪; תוספת כל התחנות: 500 ₪; המחירים כוללים מע״מ ונסיעות.', "מחיר רשמי לפי היקף תחנות.", "שלטים, ארגזי ציוד, רמקול נייד, כבלים מאריכים", "לתאם פריסת תחנות וחשמל.", "כל השנה", "תחנות,אירוע גדול", 75, 45),
            ("פעילות קהילתית אינטראקטיבית", "פעילות קהילתית תחרותית המשלבת משימות, ידע ושיתוף משפחתי.", "קהילות ומועצות", 110, 60, 220, 130, 2800, 'עד 100 ילדים: 2,800 ₪ לפני מע״מ; סך כולל מע״מ: 3,304 ₪; מהמשתתף ה-101: 14 ₪ כולל מע״מ לכל משתתף; תוספת נסיעה לכרמיאל: 450 ₪.', "מחיר רשמי לפי מדרגות והסעת ציוד.", "רמקול נייד, שלטי חידון, מעטפות משימה", "לוודא נגישות לרכב ציוד.", "כל השנה", "קהילה,אינטראקטיבי", 60, 40),
            ("מסע בעקבות ירושלים ובית המקדש", "פעילות ערכית סביב ירושלים, סמלים ומשימות חקר.", "בתי ספר וקהילות", 95, 30, 150, 100, 1700, 'מחיר דמו לצורך בדיקת המערכת בלבד.', "מחיר למפגש כולל ערכות חקר.", "כרטיסי צופן, מעטפות משימה, שלטי חידון", "להכין ערכות לפי קבוצות.", "שלושת השבועות", "ירושלים,מורשת", 45, 30),
            ("פעילות בת מצווה ערכית", "פעילות חווייתית לבנות מצווה עם משימות זהות, ערכים ויצירה.", "בנות מצווה ומשפחות", 100, 20, 100, 70, 1500, 'מחיר דמו לצורך בדיקת המערכת בלבד.', "מחיר למפגש ותוספת חומרי יצירה לפי משתתפות.", "תיקי בד, חומרי הדפסה, רמקול נייד", "לתאם שולחנות וכיסאות.", "כל השנה", "בת מצווה,ערכים", 40, 30),
        ],
        start=1,
    )
)


INVENTORY_ITEMS = tuple(
    InventorySeed(f"inventory-{i}", demo_id(6, i), name, category, unit, total, total, location, charge)
    for i, (name, category, unit, total, location, charge) in enumerate(
        [
            ("יחידות אור צבעוניות", "ציוד פעילות", "יחידה", 36, "מחסן ראשי", True),
            ("מטענים", "ציוד חשמל", "יחידה", 36, "ארון טעינה", False),
            ("סוללות נטענות", "ציוד חשמל", "סט", 48, "ארון טעינה", True),
            ("רמקול נייד", "ציוד כללי", "יחידה", 5, "מחסן ראשי", True),
            ("שלטי חידון", "ציוד משחק", "שלט", 30, "מדף משחקים", False),
            ("מעטפות משימה", "ציוד משחק", "מעטפה", 300, "מדף משחקים", False),
            ("כרטיסי צופן", "ציוד משחק", "חבילה", 40, "מדף משחקים", False),
            ("תיקי בד", "חומרי יצירה", "יחידה", 450, "מחסן יצירה", False),
            ("חומרי הדפסה", "חומרי יצירה", "סט", 80, "מחסן יצירה", False),
            ("קנבסים", "חומרי יצירה", "יחידה", 350, "מחסן יצירה", False),
            ("בסיסי חנוכייה", "חומרי יצירה", "יחידה", 250, "מחסן יצירה", False),
            ("שולחנות מתקפלים", "ציוד כללי", "יחידה", 24, "מחסן ראשי", False),
            ("כבלים מאריכים", "ציוד חשמל", "יחידה", 18, "מחסן ראשי", False),
            ("ארגזי ציוד", "ציוד כללי", "ארגז", 12, "מחסן ראשי", False),
        ],
        start=1,
    )
)


INSTRUCTION_NOTES = tuple(
    InstructionSeed(demo_id(5, i), f"activity-{activity}", title, body, order)
    for i, (activity, title, body, order) in enumerate(
        [
            (1, "טעינת ציוד", "לטעון את הציוד ערב קודם ולבדוק מטענים וסוללות.", 1),
            (1, "הקמה", "להגיע מוקדם להקמה ולוודא שטח פתוח ובטוח.", 2),
            (2, "מעטפות", "להכין מעטפות משימה וכרטיסי צופן לפי מספר קבוצות.", 1),
            (3, "הגברה", "לבדוק מקרן והגברה לפני תחילת החידון.", 1),
            (4, "חומרי יצירה", "לספור חומרי יצירה לפי מספר משתתפים ולהכין ערכות גיבוי.", 1),
            (5, "שולחנות", "לוודא מספר שולחנות מתאים לקנבסים ולחומרי קישוט.", 1),
            (6, "שטח", "לתאם שטח מוצל ונגישות לרכב ציוד.", 1),
            (7, "ערכות גיבוי", "להכין בסיסי חנוכייה נוספים וחומרי קישוט רזרביים.", 1),
            (8, "מים וחשמל", "לוודא נקודת מים קרובה ושולחן יציב להדגמה.", 1),
            (9, "פריסת תחנות", "לתאם מראש פריסת תחנות, חשמל ונקודת העמסה.", 1),
            (10, "נסיעה", "לוודא נגישות לרכב ציוד ולתאם חניה קרובה.", 1),
            (11, "ערכות חקר", "להכין ערכות לפי קבוצות ולבדוק סדר מסלול.", 1),
            (12, "שיח פתיחה", "להכין מעגל פתיחה שקט וכרטיסי משימה אישיים.", 1),
        ],
        start=1,
    )
)


REQUIREMENTS = tuple(
    RequirementSeed(demo_id(7, i), f"activity-{activity}", f"inventory-{item}", qty, per, optional, notes)
    for i, (activity, item, qty, per, optional, notes) in enumerate(
        [
            (1, 1, 12, None, False, "יחידות אור לכל תחנה"), (1, 2, 12, None, False, "מטען לכל יחידה"), (1, 3, 6, None, False, "סוללות לגיבוי"), (1, 4, 1, None, True, "הגברה לפתיחה"),
            (2, 6, 50, None, False, "מעטפות משימה לתחנות"), (2, 7, 50, None, False, "כרטיסי צופן"), (2, 5, 10, None, False, "שלט לכל תחנה"),
            (3, 5, 12, None, False, "שלטי חידון"), (3, 4, 1, None, True, "רמקול להנחיה"),
            (4, 8, 0, Decimal("1.0"), False, "תיק לכל משתתף"), (4, 9, 8, None, False, "חומרי הדפסה לעמדות"),
            (5, 10, 0, Decimal("1.0"), False, "קנבס לכל משתתף"), (5, 12, 8, None, False, "שולחנות יצירה"),
            (6, 4, 2, None, False, "הגברה לאירוע משפחות"), (6, 14, 3, None, False, "ארגזי ציוד לתחנות"),
            (7, 11, 0, Decimal("1.0"), False, "בסיס חנוכייה לכל משתתף"), (7, 12, 8, None, False, "שולחנות יצירה"),
            (8, 14, 2, None, False, "ארגזי הדגמה"), (8, 12, 3, None, False, "שולחנות להדגמה"),
            (9, 5, 20, None, False, "שלטי תחנות"), (9, 13, 6, None, True, "כבלים מאריכים"), (9, 14, 4, None, False, "ארגזי תחנות"),
            (10, 4, 2, None, False, "הגברה מרכזית"), (10, 6, 100, None, False, "מעטפות משימה"),
            (11, 6, 60, None, False, "ערכות חקר"), (11, 7, 40, None, False, "כרטיסי צופן"),
            (12, 8, 0, Decimal("1.0"), False, "תיק אישי"), (12, 9, 6, None, False, "חומרי הדפסה"),
        ],
        start=1,
    )
)


def _activity(seed_index: int, activity: int, participants: int, order: int = 1, assignment_required: bool = True, offset_minutes: int | None = None) -> BookingActivitySeed:
    offset = (order - 1) * _activity_duration(activity) if offset_minutes is None else offset_minutes
    return BookingActivitySeed(demo_id(9, seed_index * 10 + order), f"activity-{activity}", offset, _activity_duration(activity), participants, f"מתחם פעילות {order}", order, f"{DEMO_MARKER}. פעילות מספר {order}", assignment_required)


def _activity_duration(activity: int) -> int:
    return ACTIVITIES[activity - 1].duration_minutes


def _assign(seed_index: int, step: int, activity_order: int, instructor: int, action: str = "assign") -> AssignmentStep:
    return AssignmentStep(demo_id(9, seed_index * 10 + activity_order), f"instructor-{instructor}", action)


def _equip(seed_index: int, order: int, item: int, qty: int, notes: str) -> EquipmentUseSeed:
    return EquipmentUseSeed(demo_id(11, seed_index * 10 + order), f"inventory-{item}", qty, "מתוכנן", notes)


def _price(seed_index: int, order: int, desc: str, qty: int, unit: int) -> PriceComponentSeed:
    total = Decimal(qty) * Decimal(unit)
    return PriceComponentSeed(demo_id(12, seed_index * 10 + order), "פעילות", desc, Decimal(qty), Decimal(unit), total, order)


def _equipment_for(seed_index: int, activities: list[BookingActivitySeed], participants: int) -> tuple[EquipmentUseSeed, ...]:
    quantities: dict[int, tuple[int, str]] = {}
    for activity in activities:
        for requirement in REQUIREMENTS:
            if requirement.activity_key != activity.activity_key:
                continue
            inventory_number = int(requirement.inventory_key.split("-")[1])
            quantity = requirement.quantity_required
            if requirement.quantity_per_participant is not None:
                quantity += int(requirement.quantity_per_participant * Decimal(participants))
            current_quantity, _ = quantities.get(inventory_number, (0, requirement.notes))
            quantities[inventory_number] = (max(current_quantity, quantity), requirement.notes)
    return tuple(
        _equip(seed_index, order, inventory_number, quantity, notes)
        for order, (inventory_number, (quantity, notes)) in enumerate(sorted(quantities.items()), start=1)
        if quantity > 0
    )


def _price_components(seed_index: int, activities: list[BookingActivitySeed], participants: int, city: str, include_sign_quiz_addon: bool = False) -> tuple[PriceComponentSeed, ...]:
    components: list[PriceComponentSeed] = []
    order = 1
    for activity in activities:
        activity_number = int(activity.activity_key.split("-")[1])
        activity_seed = ACTIVITIES[activity_number - 1]
        quantity = Decimal("1")
        unit_price = activity_seed.base_price
        if activity_number == 5:
            quantity = Decimal(participants)
            unit_price = Decimal("34") if participants <= 100 else Decimal("28")
        elif activity_number == 4:
            quantity = Decimal(participants)
            unit_price = Decimal("32") if participants <= 100 else Decimal("27")
        elif activity_number == 7:
            quantity = Decimal(participants)
            unit_price = Decimal("38") if participants <= 80 else Decimal("33")
        elif activity_number == 12:
            quantity = Decimal(participants)
            unit_price = Decimal("45") if participants <= 80 else Decimal("39")
        components.append(PriceComponentSeed(demo_id(12, seed_index * 10 + order), "פעילות", f"{activity_seed.name} - מחיר דמו", quantity, unit_price, quantity * unit_price, order))
        order += 1
    activity_keys = {activity.activity_key for activity in activities}
    if include_sign_quiz_addon and "activity-5" in activity_keys and "activity-3" not in activity_keys:
        components.append(PriceComponentSeed(demo_id(12, seed_index * 10 + order), "תוספת", "חידון שלטים נלווה - מחיר דמו", Decimal(participants), Decimal("10"), Decimal(participants) * Decimal("10"), order))
        order += 1
    if city == "כרמיאל":
        components.append(PriceComponentSeed(demo_id(12, seed_index * 10 + order), "נסיעות", "תוספת נסיעות לכרמיאל - מחיר דמו", Decimal("1"), Decimal("450"), Decimal("450"), order))
    return tuple(components)


def _booking(i: int, customer: int, activity: int, title: str, days: int, status: str, participants: int, city: str, venue: str, *, instructor: int | None = None, second_activity: int | None = None, removed: bool = False, reassigned: int | None = None, no_instructor: bool = False, include_sign_quiz_addon: bool = False) -> BookingSeed:
    activities = [_activity(i, activity, participants, 1, not no_instructor)]
    if second_activity:
        activities.append(_activity(i, second_activity, participants, 2, not no_instructor, activities[-1].offset_minutes + activities[-1].duration_minutes))
    assignments: list[AssignmentStep] = []
    if instructor:
        assignments.append(_assign(i, 1, 1, instructor, "assign"))
        if removed:
            assignments.append(_assign(i, 2, 1, instructor, "remove"))
        if reassigned:
            assignments.append(_assign(i, 3, 1, reassigned, "assign"))
    if second_activity and instructor and not removed:
        assignments.append(_assign(i, 4, 2, ((instructor + 1 - 1) % 11) + 1, "assign"))
    customer_key = f"customer-{customer}"
    contact_key = PRIMARY_CONTACT_BY_CUSTOMER_KEY[customer_key]
    return BookingSeed(
        key=f"booking-{i}",
        id=demo_id(8, i),
        customer_key=customer_key,
        contact_key=contact_key,
        title=title,
        days_from_now=days,
        hour=9 + (i % 8),
        city=city,
        venue=venue,
        address=f"רחוב הדגמה {i}",
        participants=participants,
        audience_type="ילדים ומשפחות" if participants > 120 else "תלמידים",
        status=status,
        requires_instructor=not no_instructor,
        assignment_state="not_required" if no_instructor else "assigned",
        internal_notes=f"{DEMO_MARKER}. לתאם הגעה, פריסה וסיום מול איש הקשר.",
        customer_notes="נא להכין מים, שולחנות וגישה לחשמל לפי הצורך.",
        requires_vehicle=i % 3 == 0 or activity in {1, 9, 10},
        vehicle_notes="נדרש רכב להובלת ציוד." if i % 3 == 0 or activity in {1, 9, 10} else None,
        loading_notes="להעמיס ארגזי ציוד, רמקול וכבלים ערב קודם." if i % 3 == 0 or activity in {1, 9, 10} else None,
        activities=tuple(activities),
        assignments=tuple(assignments),
        equipment=_equipment_for(i, activities, participants),
        prices=_price_components(i, activities, participants, city, include_sign_quiz_addon),
        include_sign_quiz_addon=include_sign_quiz_addon,
    )


BOOKINGS = tuple(
    _booking(*args)
    for args in [
        (1, 1, 1, "פעילות פתיחת שנה - בית ספר נועם ירושלים", 7, BookingStatus.CONFIRMED.value, 80, "ירושלים", "אולם ספורט נועם"),
        (2, 1, 2, "מירוץ צופן שכבת ו", 18, BookingStatus.CONFIRMED.value, 95, "ירושלים", "חצר בית הספר"),
        (3, 1, 5, "סדנת סוכה להורים וילדים", 34, BookingStatus.NEW.value, 120, "ירושלים", "אולם בית ספר נועם"),
        (4, 2, 7, 'חנוכה קהילתי - מתנ"ס גבעת שמואל', 45, BookingStatus.CONFIRMED.value, 85, "גבעת שמואל", 'מתנ"ס מרכזי'),
        (5, 3, 6, "אירוע משפחות עירוני", 28, BookingStatus.CONFIRMED.value, 220, "מודיעין", "היכל התרבות"),
        (6, 4, 3, "יום שיא חסד - אולפנת אורות", 14, BookingStatus.NEW.value, 90, "בית שמש", "אולם האולפנה"),
        (7, 5, 11, "מסע ירושלים כיתות ז", 52, BookingStatus.CONFIRMED.value, 110, "פתח תקווה", "אולם תלמוד תורה"),
        (8, 6, 10, "פעילות קהילה אינטראקטיבית", 39, BookingStatus.CONFIRMED.value, 160, "אפרת", "רחבת הקהילה"),
        (9, 7, 12, "ערב בת מצווה משפחתי", 21, BookingStatus.CONFIRMED.value, 65, "רחובות", "מרכז משפחות רקפת"),
        (10, 8, 9, "מתחם תחנות לקייטנה", 11, BookingStatus.CONFIRMED.value, 150, "בית שמש", "פארק העיר"),
        (11, 1, 5, "קישוט סוכה בית ספר נועם - אירוע עבר", -12, BookingStatus.COMPLETED.value, 100, "ירושלים", "אולם בית הספר"),
        (12, 1, 4, "סדנת תיק שכבת ט - בית ספר נועם", -20, BookingStatus.COMPLETED.value, 75, "ירושלים", "כיתת אמנות"),
        (13, 11, 10, "אירוע קהילתי אזורי כרמיאל", 31, BookingStatus.CONFIRMED.value, 190, "כרמיאל", "אולם מועצה"),
        (14, 12, 8, 'סדנת שמן זית - מתנ"ס גבעתיים', -8, BookingStatus.COMPLETED.value, 70, "גבעתיים", 'מתנ"ס גבעתיים'),
        (15, 13, 1, "תפוס את האור מעלות התורה", 58, BookingStatus.CONFIRMED.value, 90, "מעלה אדומים", "חצר בית הספר"),
        (16, 14, 6, "ערב מורשת קהילתי", -35, BookingStatus.COMPLETED.value, 130, "ירושלים", "בית קהילה נווה שמחה"),
        (17, 15, 2, "מירוץ צופן לנוער איתן", 24, BookingStatus.CONFIRMED.value, 100, "מודיעין", "מרכז נוער איתן"),
        (18, 16, 9, "מתחם תחנות בין הזמנים", 6, BookingStatus.NEW.value, 140, "פתח תקווה", "פארק שכונתי"),
        (19, 1, 3, "חידון שלטים משפחות - בית ספר נועם", -3, BookingStatus.CANCELLED.value, 80, "ירושלים", "אולם קטן"),
        (20, 3, 10, "פעילות קהילתית שנדחתה", 49, BookingStatus.CANCELLED.value, 170, "מודיעין", "רחבת העירייה"),
        (21, 4, 12, "בת מצווה ערכית לאולפנה", -43, BookingStatus.CANCELLED.value, 60, "בית שמש", "אולם האולפנה"),
        (22, 5, 2, "מירוץ צופן תלמוד תורה", -28, BookingStatus.COMPLETED.value, 85, "פתח תקווה", "חצר תלמוד תורה"),
        (23, 6, 5, "סדנת סוכה קהילתית", -18, BookingStatus.COMPLETED.value, 105, "אפרת", "סוכת הקהילה"),
        (24, 7, 7, "סדנת חנוכייה משפחות", 55, BookingStatus.CONFIRMED.value, 90, "רחובות", "מרכז משפחות רקפת"),
        (25, 8, 1, "פעילות אור לקייטנה", -40, BookingStatus.COMPLETED.value, 95, "בית שמש", "פארק העיר"),
        (26, 9, 11, "מסע ירושלים אשדוד", 43, BookingStatus.NEW.value, 100, "אשדוד", "אולם בית הספר"),
        (27, 10, 5, "קישוט סוכה אולפנת הדר", 36, BookingStatus.CONFIRMED.value, 130, "רעננה", "אולם אולפנה"),
        (28, 11, 9, "מתחם תחנות כרמיאל", 57, BookingStatus.CONFIRMED.value, 150, "כרמיאל", "אולם מועצה"),
        (29, 12, 4, "סדנת תיק גבעתיים", -9, BookingStatus.COMPLETED.value, 70, "גבעתיים", 'מתנ"ס גבעתיים'),
        (30, 13, 3, "חידון שלטים מעלות התורה", 16, BookingStatus.CONFIRMED.value, 75, "מעלה אדומים", "אולם בית הספר"),
        (31, 14, 6, "אירוע משפחות נווה שמחה", 22, BookingStatus.CANCELLED.value, 180, "ירושלים", "רחבת הקהילה"),
        (32, 15, 2, "מירוץ צופן ערב נוער", 44, BookingStatus.CONFIRMED.value, 90, "מודיעין", "מרכז נוער איתן"),
    ]
)

BOOKINGS = tuple(
    booking
    if booking.key not in {"booking-5", "booking-8", "booking-13", "booking-28"}
    else BookingSeed(
        **{
            **booking.__dict__,
            "activities": (
                *booking.activities,
                BookingActivitySeed(
                    **{
                        **_activity(
                            int(booking.key.split("-")[1]),
                            3,
                            min(booking.participants, 90),
                            2,
                            True,
                            booking.activities[-1].offset_minutes + booking.activities[-1].duration_minutes,
                        ).__dict__,
                        "notes": f"{DEMO_MARKER}. חידון שלטים בסבבים לקבוצה מתוך כלל המשתתפים.",
                    }
                ),
            ),
        }
    )
    for booking in BOOKINGS
)

BOOKINGS = tuple(
    booking
    if booking.key not in {"booking-1", "booking-2", "booking-4", "booking-5", "booking-7", "booking-8", "booking-9", "booking-10", "booking-13", "booking-15", "booking-17", "booking-24", "booking-27", "booking-28", "booking-30", "booking-32"}
    else BookingSeed(**{**booking.__dict__, "assignments": booking.assignments or (_assign(int(booking.key.split("-")[1]), 1, 1, ((int(booking.key.split("-")[1]) - 1) % 11) + 1),)})
    for booking in BOOKINGS
)

def _with_assignment_history(booking: BookingSeed) -> BookingSeed:
    if booking.key == "booking-15":
        return BookingSeed(**{**booking.__dict__, "assignments": (_assign(15, 1, 1, 3), _assign(15, 2, 1, 3, "remove"), _assign(15, 3, 1, 6, "assign"))})
    if booking.key == "booking-17":
        return BookingSeed(**{**booking.__dict__, "assignments": (_assign(17, 1, 1, 4), _assign(17, 2, 1, 4, "remove"), _assign(17, 3, 1, 5, "assign"))})
    return booking


BOOKINGS = tuple(_with_assignment_history(booking) for booking in BOOKINGS)


BOOKINGS = tuple(
    booking
    if booking.key not in {"booking-10", "booking-18"}
    else BookingSeed(**{**booking.__dict__, "assignment_state": "not_required", "assignments": ()})
    for booking in BOOKINGS
)


UNASSIGNED_NOTES = {
    "booking-3": "טרם שובצה מדריכה",
    "booking-6": "פתוח לשיבוץ",
    "booking-24": "מחפשות מדריכה בעלת ניסיון בסדנאות יצירה",
    "booking-27": "נדרשת מדריכה מאזור ירושלים",
    "booking-30": "פתוח לשיבוץ",
}


BOOKINGS = tuple(
    booking
    if booking.key not in UNASSIGNED_NOTES
    else BookingSeed(
        **{
            **booking.__dict__,
            "assignment_state": "unassigned",
            "assignments": (),
            "internal_notes": f"{DEMO_MARKER}. {UNASSIGNED_NOTES[booking.key]}.",
        }
    )
    for booking in BOOKINGS
)


def _assignment_for_all_required_activities(booking: BookingSeed) -> tuple[AssignmentStep, ...]:
    assignments = list(booking.assignments)
    active_assignments: set[tuple[UUID, str]] = set()
    for step in assignments:
        pair = (step.booking_activity_id, step.instructor_key)
        if step.action == "assign":
            active_assignments.add(pair)
        else:
            active_assignments.discard(pair)
    booking_number = int(booking.key.split("-")[1])
    for activity in booking.activities:
        if not activity.assignment_required or any(activity.id == activity_id for activity_id, _ in active_assignments):
            continue
        instructor = ((booking_number + activity.sort_order - 2) % len(INSTRUCTORS)) + 1
        step = len(assignments) + 1
        assignments.append(_assign(booking_number, step, activity.sort_order, instructor))
        active_assignments.add((activity.id, f"instructor-{instructor}"))
    return tuple(assignments)


def _normalized_booking(booking: BookingSeed) -> BookingSeed:
    booking_number = int(booking.key.split("-")[1])
    updates = dict(booking.__dict__)
    if booking.key in {"booking-3", "booking-11"}:
        updates["include_sign_quiz_addon"] = True
    if booking.assignment_state == "not_required":
        activities = tuple(
            BookingActivitySeed(**{**activity.__dict__, "assignment_required": False})
            for activity in booking.activities
        )
        updates.update(
            requires_instructor=False,
            assignment_state="not_required",
            activities=activities,
            assignments=(),
            internal_notes=f"{DEMO_MARKER}. מתחם הפעלה עצמית ללא שיבוץ מדריך.",
        )
    elif booking.assignment_state == "unassigned":
        activities = tuple(
            BookingActivitySeed(**{**activity.__dict__, "assignment_required": True})
            for activity in booking.activities
        )
        updates.update(
            requires_instructor=True,
            activities=activities,
            assignments=(),
        )
    elif booking.assignment_state == "assigned":
        updates["requires_instructor"] = True
        updates["assignments"] = _assignment_for_all_required_activities(booking)
    if booking.key in {"booking-1", "booking-2", "booking-4", "booking-5", "booking-7"}:
        assignments = list(updates.get("assignments", booking.assignments))
        first_activity = updates.get("activities", booking.activities)[0]
        if first_activity.assignment_required and not any(step.booking_activity_id == first_activity.id and step.instructor_key == "instructor-1" and step.action == "assign" for step in assignments):
            assignments.append(_assign(booking_number, len(assignments) + 1, 1, 1))
        updates["assignments"] = tuple(assignments)
    updated = BookingSeed(**updates)
    return BookingSeed(
        **{
            **updated.__dict__,
            "equipment": _equipment_for(booking_number, list(updated.activities), updated.participants),
            "prices": _price_components(booking_number, list(updated.activities), updated.participants, updated.city, updated.include_sign_quiz_addon),
        }
    )


BOOKINGS = tuple(_normalized_booking(booking) for booking in BOOKINGS)
