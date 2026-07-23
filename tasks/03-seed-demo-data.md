Task 03 - Seed Demo Data

Goal

Add realistic Hebrew demo data to the existing PostgreSQL database so the system can be tested with meaningful content.

The system is intended to be used in Hebrew, so all demo business data should be in Hebrew.

The frontend must not connect directly to the database. All database access remains owned by the FastAPI backend.

Current State

Task 02 is complete:

Backend connects successfully to Supabase PostgreSQL.

/system/db-status returns database reachable.

/system/init-db creates the required tables.

/system/schema-summary confirms all expected tables exist.

Database environment variables are stored only under backend/.env.

Required Work

Create a backend seed script that inserts demo data into the existing tables.

Suggested file:

backend/app/db/seed_demo_data.py

The script should use the existing backend database connection code.

Tables To Seed

Seed realistic demo data for these tables:

customers

customer_contacts

instructors

activities

activity_instruction_notes

inventory_items

activity_equipment_requirements

bookings

booking_activities

booking_instructors

booking_equipment_items

booking_price_components

Demo Data Requirements

Use realistic Hebrew data for the business "חוויה עם נשמה".

Customers

Create several demo customers, for example:

בית ספר נועם ירושלים

מתנ"ס גבעת שמואל

עיריית מודיעין - אגף תרבות תורנית

אולפנת אורות

ישיבת בני עקיבא רעננה

קייטנת קיץ בית שמש

תלמוד תורה דרכי אבות

Customer types can include:

בית ספר

מתנ"ס

עירייה

ישיבה

אולפנה

קייטנה

Customer Contacts

Each customer should have at least one contact person.

Use Hebrew names and realistic roles, for example:

רכזת חברתית

מנהל בית ספר

רכז תרבות

מזכירות

מנהל קייטנה

Do not use real private customer data.

Phone numbers should be fake but realistic Israeli-style numbers, for example:

050-0000001

052-0000002

054-0000003

Emails should be fake demo emails, for example:

demo1@example.com

demo2@example.com

Instructors

Add several instructors with Hebrew names.

Example names:

מיכל כהן

שירה לוי

תמר ישראלי

הדס אברהם

יעל מזרחי

נועה שפירא

Use only fields that already exist in the schema.

Activities

Add the main activities of the business:

תפוס את האור

מירוץ הצופן

חידון שלטים

סדנת תיק בעיצוב אישי

קישוט סוכה על קנבס

Each activity should include realistic Hebrew descriptions, duration, pricing notes if the schema supports it, and default participant ranges if relevant.

Example activity descriptions:

פעילות אתגרית עם ציוד לייזר, משימות קבוצתיות וניקוד.

משחק תחנות לפענוח כתבי חידה וצפנים.

חידון שלטים קבוצתי עם שאלות ידע, זריזות ושיתוף פעולה.

סדנת יצירה שבה כל משתתף מעצב תיק אישי.

סדנת יצירה לחג הסוכות על קנבס אישי.

Activity Instruction Notes

Add Hebrew instruction notes for activities.

For תפוס את האור:

לבדוק שכל ערכות הלייזר טעונות ערב קודם.

להביא סוללות גיבוי ומטענים.

לוודא שיש שטח פתוח ובטיחותי לפעילות.

For סדנת תיק בעיצוב אישי:

להכין מראש עמדת חומרים לכל קבוצה.

לבדוק שיש מספיק טושים, שבלונות ותיקים.

לשמור כמה תוצרים רזרביים למקרה של תקלה.

Inventory Items

Add realistic equipment items, for example:

ערכת לייזר

מטען לערכת לייזר

סוללות נטענות

שלטי חידון

כרטיסי שאלות

תיקי בד להדפסה

טושים לבד

שבלונות עיצוב

מעטפות משימה

כרטיסי צופן

קנבסים לסוכה

רמקול נייד

כבל מאריך

ארגז ציוד כללי

Activity Equipment Requirements

Connect activities to required inventory items.

Examples:

תפוס את האור requires:

ערכת לייזר

מטען לערכת לייזר

סוללות נטענות

רמקול נייד

חידון שלטים requires:

שלטי חידון

כרטיסי שאלות

רמקול נייד

סדנת תיק בעיצוב אישי requires:

תיקי בד להדפסה

טושים לבד

שבלונות עיצוב

Bookings

Create several realistic future bookings.

Use Hebrew event titles and notes.

Examples:

פעילות פתיחת שנה - בית ספר נועם ירושלים

יום שיא חסד - אולפנת אורות

פעילות חנוכה - מתנ"ס גבעת שמואל

קייטנת קיץ - בית שמש

ערב משפחות - עיריית מודיעין

Each booking should be connected to a customer.

Include realistic data such as:

event date

location

participant count

status

internal notes

loading notes

whether transportation/loading vehicle is needed, if supported by schema

Statuses can be:

מתוכנן

אושר

בוצע

ממתין לאישור

Booking Activities

Each booking should include one or more activities.

Examples:

Booking 1: תפוס את האור

Booking 2: חידון שלטים + מירוץ הצופן

Booking 3: סדנת תיק בעיצוב אישי

Booking 4: קישוט סוכה על קנבס

Booking Instructors

Assign instructors to bookings.

Each booking should have at least one instructor.

Some larger bookings can have two instructors.

Booking Equipment Items

Assign equipment items to bookings according to the activities.

Use realistic quantities.

Examples:

12 ערכות לייזר

12 מטענים

80 תיקי בד

100 קנבסים

10 שלטי חידון

50 מעטפות משימה

Booking Price Components

Add price lines for bookings.

Examples:

פעילות תפוס את האור - 1,800 ש"ח

חידון שלטים - 900 ש"ח

סדנת תיק בעיצוב אישי - 34 ש"ח למשתתף

תוספת נסיעות והובלה - 250 ש"ח

הנחת כמות - מינוס 300 ש"ח

Use Hebrew labels.

Idempotency Requirement

The seed script must be safe to run more than once.

Choose one of these approaches:

Delete only demo data before inserting it again.

Use stable demo identifiers and upsert logic.

Do not delete non-demo real data.

Recommended approach:

Add a clear marker to demo records where possible, such as notes containing נתוני דמה.

Before inserting, delete only records created by the seed script.

If the current schema does not support a clear marker in every table, use stable IDs in the script.

Running The Script

Add a simple way to run the seed script from PowerShell.

Example:

.venv\Scripts\python.exe -m backend.app.db.seed_demo_data

The script should print a clear success message, for example:

Demo data seeded successfully.
Customers: 7
Contacts: 9
Activities: 5
Bookings: 5

Documentation

Update the Task 03 documentation with:

What the seed script does.

How to run it.

Confirmation that all demo data is Hebrew.

Confirmation that no real private customer data is used.

Confirmation that the script is safe to run multiple times.

Suggested documentation file:

docs/piv/03-seed-demo-data.md

Validation

After implementing, run:

.venv\Scripts\python.exe -m compileall backend desktop_client

Then run the seed script:

.venv\Scripts\python.exe -m backend.app.db.seed_demo_data

Then verify from the database or from a temporary backend check that records were inserted into:

customers

customer_contacts

activities

inventory_items

bookings

Acceptance Criteria

Task 03 is complete when:

A backend seed script exists.

The script uses the existing backend DB connection code.

Demo data is inserted into all relevant tables.

All business-facing demo data is in Hebrew.

No real private customer data is used.

The script can be run multiple times safely.

Documentation explains how to run the script.

Backend validation passes.