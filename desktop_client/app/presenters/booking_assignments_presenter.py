from desktop_client.app.api.client import ApiError,ApiErrorKind
class BookingAssignmentsPresenter:
    def __init__(self,view,assignment_service,instructor_service,*,refresh_booking=lambda _id:None,refresh_related=lambda:None):self.view=view;self.assignment_service=assignment_service;self.instructor_service=instructor_service;self.refresh_booking=refresh_booking;self.refresh_related=refresh_related;self.booking_id=None;self.model=None;self.submitting=False;self.selector=None
    def select_booking(self,booking_id):self.booking_id=booking_id;self.load()
    def load(self):
        if not self.booking_id:return
        self.view.set_assignments_loading(True)
        try:self.model=self.assignment_service.assignments(self.booking_id);self.view.show_assignments(self.model["activities"])
        except Exception as e:self.view.show_assignments_error(self.message(e),retriable=isinstance(e,ApiError) and e.retriable)
        finally:self.view.set_assignments_loading(False)
    def begin_assign(self,activity):
        if self.submitting or not self.model:return
        self.selector=self.view.open_instructor_selector(activity,self.load_selector,lambda instructor:self.assign(activity,instructor));self.load_selector({"search":None,"city":None,"is_active":True,"order_by":"full_name","limit":25,"offset":0})
    def load_selector(self,filters):
        try:
            filters={**filters,"is_active":True};p=self.instructor_service.list_instructors(filters);assigned={str(x["instructor_id"]) for x in next((a["assignments"] for a in self.model["activities"] if a["booking_activity_id"]==self.selector.activity["booking_activity_id"]),[])};items=[{**x,"_already_assigned":str(x["id"]) in assigned} for x in p["items"]];self.selector.show_instructors(items,offset=filters.get("offset",0),count=len(p["items"]))
        except Exception as e:self.selector.show_error(self.message(e),retriable=isinstance(e,ApiError) and e.retriable)
    def assign(self,activity,instructor):self._command(lambda:self.assignment_service.assign(self.booking_id,activity["booking_activity_id"],instructor["id"],self.model["version"]),"המדריך שויך בהצלחה.")
    def remove(self,activity,assignment):
        if self.view.confirm_assignment_removal(assignment["instructor_name"],activity["activity_name"]):self._command(lambda:self.assignment_service.remove(self.booking_id,activity["booking_activity_id"],assignment["instructor_id"],self.model["version"]),"שיוך המדריך הוסר. היסטוריית האירועים נשמרה.")
    def _command(self,op,msg):
        if self.submitting:return
        self.submitting=True;self.view.set_assignments_loading(True)
        try:op();self.load();self.refresh_booking(self.booking_id);self.refresh_related();self.view.show_success(msg);self.selector.close_success() if self.selector else None
        except Exception as e:self.view.show_assignments_error(self.message(e),retriable=isinstance(e,ApiError) and e.retriable);self.load() if isinstance(e,ApiError) and e.status_code in {400,404,409,422} else None
        finally:self.submitting=False;self.view.set_assignments_loading(False)
    @staticmethod
    def message(e):
        if isinstance(e,ApiError):
            if e.status_code==409:return "ההזמנה השתנתה. הנתונים רועננו; יש לאשר את הפעולה מחדש."
            if e.status_code in {400,422}:return f"לא ניתן לשנות את השיוך: {e}"
            if e.status_code==403:return "אין הרשאה לנהל שיוכי מדריכים."
            if e.status_code==404:return "ההזמנה, הפעילות או המדריך אינם קיימים עוד."
        return str(e)
