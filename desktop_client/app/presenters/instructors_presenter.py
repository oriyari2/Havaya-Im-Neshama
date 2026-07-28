from __future__ import annotations
import logging,re
from desktop_client.app.api.client import ApiError,ApiErrorKind
from desktop_client.app.presenters.instructor_formatting import instructor_details,instructor_row
logger=logging.getLogger(__name__); EMAIL=re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
def validate_instructor(values):
    name=str(values.get("full_name") or "").strip()
    if not name:raise ValueError("יש להזין שם מדריך.")
    email=str(values.get("email") or "").strip().lower() or None
    if email and not EMAIL.match(email):raise ValueError("כתובת הדוא״ל אינה תקינה.")
    return {"full_name":name,"phone":str(values.get("phone") or "").strip() or None,"email":email,"city":str(values.get("city") or "").strip() or None,"notes":str(values.get("notes") or "").strip() or None,"is_active":bool(values.get("is_active",True))}
class InstructorsPresenter:
    def __init__(self,view,service,limit=25):self.view=view;self.service=service;self.filters={"search":None,"city":None,"is_active":None,"order_by":"full_name","limit":limit,"offset":0};self.selected_id=None;self.selected=None;self.loading=False;self.submitting=False
    def load(self):
        if self.loading:return
        self.loading=True;self.view.set_loading(True)
        try:
            p=self.service.list_instructors(dict(self.filters));items=p["items"];self.view.show_instructors([instructor_row(x) for x in items],offset=self.filters["offset"],count=len(items),filtered=any(self.filters[k] not in (None,"") for k in ("search","city","is_active")))
            ids={str(x["id"]) for x in items}
            if self.selected_id in ids:self.view.select_instructor(self.selected_id)
            elif self.selected_id:self.selected_id=self.selected=None;self.view.clear_details()
        except Exception as e:self._error(e)
        finally:self.loading=False;self.view.set_loading(False)
    def apply_filters(self,v):self.filters.update({k:v for k,v in v.items() if k in {"search","city","is_active","order_by"}});self.filters["offset"]=0;self.load()
    def page(self,offset,limit):self.filters.update(offset=max(0,offset),limit=limit);self.load()
    def retry(self):self.load()
    def select(self,i):
        self.selected_id=i;self.view.set_loading(True)
        try:self.selected=self.service.instructor(i);self.view.show_details(instructor_details(self.selected),self.selected)
        except ApiError as e:
            if e.kind==ApiErrorKind.NOT_FOUND:self.selected_id=self.selected=None;self.view.clear_details();self.view.show_error("המדריך שנבחר אינו קיים עוד. הרשימה רועננה.");self.load()
            else:self._error(e)
        except Exception as e:self._error(e)
        finally:self.view.set_loading(False)
    def begin_create(self):self.view.open_form(None,self.submit_create)
    def begin_edit(self):
        if self.selected:self.view.open_form(self.selected,self.submit_edit)
    def submit_create(self,v,f):self._submit(v,f,None)
    def submit_edit(self,v,f):self._submit(v,f,self.selected_id)
    def _submit(self,v,f,i):
        if self.submitting:return
        try:p=validate_instructor(v)
        except ValueError as e:f.show_error(str(e));return
        self.submitting=True;f.set_submitting(True)
        try:x=self.service.update_instructor(i,p) if i else self.service.create_instructor(p);self.selected_id=str(x["id"]);f.close_success();self.view.show_success("המדריך נשמר בהצלחה.");self.load();self.select(self.selected_id)
        except Exception as e:
            f.show_error(self.message(e))
            if isinstance(e,ApiError) and e.kind==ApiErrorKind.CONFLICT and self.selected_id:self.select(self.selected_id)
        finally:self.submitting=False;f.set_submitting(False)
    def deactivate(self):
        if self.selected and self.selected.get("is_active") and self.view.confirm_deactivation(self.selected["full_name"]):self._mutate(lambda:self.service.deactivate_instructor(self.selected_id),"המדריך הושבת.")
    def reactivate(self):
        if self.selected and not self.selected.get("is_active"):self._mutate(lambda:self.service.reactivate_instructor(self.selected_id),"המדריך הופעל מחדש.")
    def _mutate(self,op,msg):
        if self.submitting:return
        self.submitting=True
        try:x=op();i=str(x["id"]);self.selected_id=i;self.view.show_success(msg);self.load();self.select(i) if self.selected_id else None
        except Exception as e:self._error(e)
        finally:self.submitting=False
    def _error(self,e):
        if not isinstance(e,ApiError):logger.error("Unexpected instructor failure",exc_info=(type(e),e,e.__traceback__))
        self.view.show_error(self.message(e),retriable=isinstance(e,ApiError) and e.retriable,permission=isinstance(e,ApiError) and e.kind==ApiErrorKind.PERMISSION)
    @staticmethod
    def message(e):
        if isinstance(e,ApiError):
            if e.kind==ApiErrorKind.PERMISSION:return "אין הרשאה לצפות במדריכים או לשנות אותם."
            if e.kind==ApiErrorKind.CONFLICT:return "כתובת הדוא״ל כבר משויכת למדריך אחר."
            if e.kind==ApiErrorKind.CONNECTION:return "לא ניתן להתחבר לשרת. נסו שוב."
            if e.kind==ApiErrorKind.SERVER:return "השרת לא הצליח להשלים את הפעולה. נסו שוב."
        return str(e) or "הפעולה נכשלה."
class InstructorProfilePresenter:
    def __init__(self,view,service):self.view=view;self.service=service
    def load(self):
        self.view.set_loading(True)
        try:x=self.service.my_profile();self.view.show_profile(instructor_details(x))
        except Exception as e:self.view.show_error(InstructorsPresenter.message(e),retriable=isinstance(e,ApiError) and e.retriable,permission=isinstance(e,ApiError) and e.kind==ApiErrorKind.PERMISSION)
        finally:self.view.set_loading(False)
    def retry(self):self.load()
