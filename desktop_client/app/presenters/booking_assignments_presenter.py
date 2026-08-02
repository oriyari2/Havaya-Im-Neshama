from desktop_client.app.api.client import ApiError
from desktop_client.app.models.operation import OperationExecutor, PresenterOperations


class BookingAssignmentsPresenter:
    def __init__(self, view, assignment_service, instructor_service, *, refresh_booking=lambda _id: None, refresh_related=lambda: None, confirm_after_assignment=lambda _booking: None, executor: OperationExecutor | None = None):
        self.view, self.assignment_service, self.instructor_service = view, assignment_service, instructor_service
        self.refresh_booking, self.refresh_related = refresh_booking, refresh_related
        self.confirm_after_assignment = confirm_after_assignment
        self.booking_id = None
        self.model = None
        self.submitting = False
        self.selector = None
        self._operations = PresenterOperations(executor, "booking_assignments")

    def invalidate_requests(self):
        self._operations.invalidate()
        self.view.set_assignments_loading(False)

    def select_booking(self, booking_id):
        self.booking_id = booking_id
        self.load()

    def load(self):
        if not self.booking_id:
            return
        booking_id = self.booking_id
        context = self._operations.replace("list")
        self.view.set_assignments_loading(True)

        def success(model):
            if self._operations.is_current(context) and self.booking_id == booking_id:
                self.model = model
                self.view.show_assignments(model["activities"])

        def failure(exc):
            if self._operations.is_current(context):
                self.view.show_assignments_error(self.message(exc), retriable=isinstance(exc, ApiError) and exc.retriable)

        def finished():
            if self._operations.finish(context):
                self.view.set_assignments_loading(False)

        self._operations.executor.submit(context, lambda: self.assignment_service.assignments(booking_id), success, failure, finished)

    def begin_assign(self, activity):
        if self.submitting or not self.model:
            return
        self.selector = self.view.open_instructor_selector(activity, self.load_selector, lambda instructor: self.assign(activity, instructor))
        self.load_selector({"search": None, "city": None, "is_active": True, "order_by": "full_name", "limit": 25, "offset": 0})

    def begin_assign_and_confirm(self, activity):
        if self.submitting or not self.model:
            return
        if activity.get("assignments"):
            self.confirm_after_assignment(
                {"id": self.booking_id, "version": self.model["version"], "status": "NEW"}
            )
            return
        self.selector = self.view.open_instructor_selector(
            activity,
            self.load_selector,
            lambda instructor: self.assign(activity, instructor, self.confirm_after_assignment),
        )
        self.load_selector({"search": None, "city": None, "is_active": True, "order_by": "full_name", "limit": 25, "offset": 0})

    def begin_replace(self, activity, assignment):
        if self.submitting or not self.model:
            return
        self.selector = self.view.open_instructor_selector(
            activity,
            self.load_selector,
            lambda instructor: self.replace(activity, assignment, instructor),
        )
        self.load_selector({"search": None, "city": None, "is_active": True, "order_by": "full_name", "limit": 25, "offset": 0})

    def replace(self, activity, assignment, instructor):
        def operation():
            removed = self.assignment_service.remove(
                self.booking_id,
                activity["booking_activity_id"],
                assignment["instructor_id"],
                self.model["version"],
            )
            return self.assignment_service.assign(
                self.booking_id,
                activity["booking_activity_id"],
                instructor["id"],
                int(removed["version"]),
            )

        self._command(operation, "המדריך הוחלף בהצלחה.")

    def assign_after_creation(self, booking, instructor_id):
        booking_id = str(booking["id"])
        context = self._operations.replace("post_create_assignment")

        def success(model):
            if not self._operations.is_current(context):
                return
            self.booking_id, self.model = booking_id, model
            activities = model.get("activities") or []
            if not activities:
                self.view.show_assignments_error("לא נמצאה פעילות להזמנה שנוצרה.", retriable=False)
                return
            self.assign(activities[0], {"id": instructor_id})

        self._operations.executor.submit(
            context,
            lambda: self.assignment_service.assignments(booking_id),
            success,
            lambda exc: self.view.show_assignments_error(self.message(exc), retriable=isinstance(exc, ApiError) and exc.retriable),
            lambda: self._operations.finish(context),
        )

    def load_selector(self, filters):
        normalized = {**filters, "is_active": True}
        context = self._operations.replace("selector")

        def success(payload):
            if not self._operations.is_current(context) or self.selector is None:
                return
            assigned = {str(item["instructor_id"]) for item in next((item["assignments"] for item in self.model["activities"] if item["booking_activity_id"] == self.selector.activity["booking_activity_id"]), [])}
            items = [{**item, "_already_assigned": str(item["id"]) in assigned} for item in payload["items"]]
            self.selector.show_instructors(items, offset=normalized.get("offset", 0), count=len(items))

        def failure(exc):
            if self._operations.is_current(context) and self.selector is not None:
                self.selector.show_error(self.message(exc), retriable=isinstance(exc, ApiError) and exc.retriable)

        self._operations.executor.submit(context, lambda: self.instructor_service.list_instructors(normalized), success, failure, lambda: self._operations.finish(context))

    def assign(self, activity, instructor, on_success=None):
        self._command(lambda: self.assignment_service.assign(self.booking_id, activity["booking_activity_id"], instructor["id"], self.model["version"]), "המדריך שויך בהצלחה.", on_success)

    def remove(self, activity, assignment):
        if self.view.confirm_assignment_removal(assignment["instructor_name"], activity["activity_name"]):
            self._command(lambda: self.assignment_service.remove(self.booking_id, activity["booking_activity_id"], assignment["instructor_id"], self.model["version"]), "שיוך המדריך הוסר. היסטוריית האירועים נשמרה.")

    def _command(self, operation, message, on_success=None):
        if self.submitting:
            return
        context = self._operations.begin("mutation")
        if context is None:
            return
        booking_id = self.booking_id
        self.submitting = True
        self.view.set_assignments_loading(True)

        def success(result):
            if not self._operations.is_current(context):
                return
            self.load()
            self.refresh_booking(booking_id)
            self.refresh_related()
            self.view.show_success(message)
            if self.selector:
                self.selector.close_success()
            if on_success is not None:
                on_success(result)

        def failure(exc):
            if not self._operations.is_current(context):
                return
            self.view.show_assignments_error(self.message(exc), retriable=isinstance(exc, ApiError) and exc.retriable)
            if isinstance(exc, ApiError) and exc.status_code in {400, 404, 409, 422}:
                self.load()

        def finished():
            if self._operations.finish(context):
                self.submitting = False
                self.view.set_assignments_loading(False)

        self._operations.executor.submit(context, operation, success, failure, finished)

    @staticmethod
    def message(exc):
        if isinstance(exc, ApiError):
            if exc.status_code == 409:
                return "ההזמנה השתנתה. הנתונים רועננו; יש לאשר את הפעולה מחדש."
            if exc.status_code in {400, 422}:
                return f"לא ניתן לשנות את השיוך: {exc}"
            if exc.status_code == 403:
                return "אין הרשאה לנהל שיוכי מדריכים."
            if exc.status_code == 404:
                return "ההזמנה, הפעילות או המדריך אינם קיימים עוד."
        return "לא ניתן להשלים את פעולת השיוך. נסו שוב."
