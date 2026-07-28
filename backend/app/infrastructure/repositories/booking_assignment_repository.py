from uuid import UUID

def get_header(cur,booking_id:UUID):
    cur.execute("SELECT id AS booking_id, version, requires_instructor FROM bookings WHERE id=%s;",(booking_id,));return cur.fetchone()
def list_activities(cur,booking_id:UUID):
    cur.execute("""SELECT ba.id AS booking_activity_id,ba.activity_id,a.name AS activity_name,(b.requires_instructor AND b.status IN ('NEW','CONFIRMED') AND b.event_at>=now() AND NOT EXISTS (SELECT 1 FROM booking_instructors bi WHERE bi.booking_activity_id=ba.id AND bi.active=true)) AS assignment_required FROM booking_activities ba JOIN bookings b ON b.id=ba.booking_id JOIN activities a ON a.id=ba.activity_id WHERE ba.booking_id=%s ORDER BY ba.sort_order,ba.created_at,ba.id;""",(booking_id,));return list(cur.fetchall())
def list_active_assignments(cur,booking_id:UUID):
    cur.execute("""SELECT bi.booking_activity_id,bi.instructor_id,i.full_name AS instructor_name,i.city AS instructor_city,bi.assigned_at FROM booking_instructors bi JOIN booking_activities ba ON ba.id=bi.booking_activity_id JOIN instructors i ON i.id=bi.instructor_id WHERE ba.booking_id=%s AND bi.active=true ORDER BY bi.booking_activity_id,i.full_name,i.id;""",(booking_id,));return list(cur.fetchall())
def get_open_event_header(cur,booking_id:UUID,now):
    cur.execute("""SELECT b.id AS booking_id,b.event_at,b.city,b.venue,b.status,b.requires_instructor,b.version FROM bookings b WHERE b.id=%s AND b.event_at>=%s AND b.status IN ('NEW','CONFIRMED') AND b.requires_instructor=true AND EXISTS (SELECT 1 FROM booking_activities ba WHERE ba.booking_id=b.id AND NOT EXISTS (SELECT 1 FROM booking_instructors bi WHERE bi.booking_activity_id=ba.id AND bi.active=true));""",(booking_id,now));return cur.fetchone()
