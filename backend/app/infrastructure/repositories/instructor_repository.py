from __future__ import annotations
from uuid import UUID

COLUMNS="id, full_name, phone, email, city, notes, is_active, created_at, updated_at"
FIELDS=("full_name","phone","email","city","notes","is_active")

def list_instructors(cur, *, search, city, is_active, order_by, limit, offset):
    clauses=[]; params=[]
    if search and search.strip():
        value=f"%{search.strip()}%"; clauses.append("(full_name ILIKE %s OR email ILIKE %s OR phone ILIKE %s OR city ILIKE %s)"); params.extend([value]*4)
    if city and city.strip(): clauses.append("city ILIKE %s"); params.append(f"%{city.strip()}%")
    if is_active is not None: clauses.append("is_active = %s"); params.append(is_active)
    sort={"full_name":"full_name ASC, id ASC","created_at":"created_at DESC, id ASC"}[order_by]
    where=f"WHERE {' AND '.join(clauses)}" if clauses else ""
    cur.execute(f"SELECT {COLUMNS} FROM instructors {where} ORDER BY {sort} LIMIT %s OFFSET %s;",[*params,limit,offset]); return list(cur.fetchall())

def get_instructor(cur,instructor_id:UUID): cur.execute(f"SELECT {COLUMNS} FROM instructors WHERE id=%s;",(instructor_id,)); return cur.fetchone()
def lock_instructor(cur,instructor_id:UUID): cur.execute(f"SELECT {COLUMNS} FROM instructors WHERE id=%s FOR UPDATE;",(instructor_id,)); return cur.fetchone()
def instructor_delete_dependencies(cur,instructor_id:UUID):
    cur.execute("""SELECT
        EXISTS (SELECT 1 FROM users WHERE instructor_id=%s) AS has_user,
        EXISTS (SELECT 1 FROM booking_instructors WHERE instructor_id=%s) AS has_assignment_history,
        EXISTS (SELECT 1 FROM booking_events WHERE event_data ->> 'instructor_id'=%s) AS has_event_history;""",
        (instructor_id,instructor_id,str(instructor_id)))
    return cur.fetchone()
def delete_instructor(cur,instructor_id:UUID): cur.execute("DELETE FROM instructors WHERE id=%s RETURNING id;",(instructor_id,)); return cur.fetchone() is not None
def get_by_email(cur,email:str,exclude_id:UUID|None=None):
    sql=f"SELECT {COLUMNS} FROM instructors WHERE lower(email)=lower(%s)"; params=[email]
    if exclude_id: sql+=" AND id<>%s"; params.append(exclude_id)
    cur.execute(sql+" LIMIT 1;",params); return cur.fetchone()
def create_instructor(cur,data):
    cur.execute(f"INSERT INTO instructors (full_name,phone,email,city,notes,is_active) VALUES (%s,%s,%s,%s,%s,%s) RETURNING {COLUMNS};",tuple(data[x] for x in FIELDS)); return cur.fetchone()
def update_instructor(cur,instructor_id,data):
    fields=[x for x in FIELDS if x in data]; cur.execute(f"UPDATE instructors SET {', '.join(f'{x}=%s' for x in fields)}, updated_at=now() WHERE id=%s RETURNING {COLUMNS};",[*[data[x] for x in fields],instructor_id]); return cur.fetchone()
