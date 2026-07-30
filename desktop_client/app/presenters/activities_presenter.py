from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Callable, Protocol

from desktop_client.app.api.client import ApiError, ApiErrorKind
from desktop_client.app.presenters.activity_formatting import activity_details, activity_row
from desktop_client.app.media_config import MAX_PREVIEW_CACHE_ENTRIES


logger = logging.getLogger(__name__)


class FormPort(Protocol):
    def set_submitting(self, submitting: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def close_success(self) -> None: ...


class ActivityServicePort(Protocol):
    def list_activities(self, filters: dict[str, object]) -> dict: ...
    def activity(self, activity_id: str) -> dict: ...
    def create_activity(self, payload: dict[str, object]) -> dict: ...
    def update_activity(self, activity_id: str, payload: dict[str, object]) -> dict: ...
    def deactivate_activity(self, activity_id: str) -> dict: ...
    def reactivate_activity(self, activity_id: str) -> dict: ...
    def upload_image(self, activity_id: str, file_path: str) -> dict: ...
    def delete_image(self, activity_id: str, image_id: str) -> dict: ...
    def preview_bytes(self, secure_url: str) -> bytes: ...


def validate_activity(values: dict[str, object]) -> dict[str, object]:
    name = str(values.get("name") or "").strip()
    if not name:
        raise ValueError("יש להזין שם פעילות.")
    result: dict[str, object] = {"name": name}
    for key in ("description", "target_audience", "pricing_rule", "required_equipment", "preparation_notes", "season", "tags"):
        result[key] = str(values.get(key) or "").strip() or None
    for key, label in (("duration_minutes", "משך"), ("recommended_capacity", "קיבולת")):
        raw = str(values.get(key) or "").strip()
        if not raw:
            result[key] = None
            continue
        try:
            number = int(raw)
        except ValueError as exc:
            raise ValueError(f"{label} חייב להיות מספר שלם.") from exc
        if number <= 0:
            raise ValueError(f"{label} חייב להיות גדול מאפס.")
        result[key] = number
    result["is_active"] = bool(values.get("is_active", True))
    return result


class ActivitiesPresenter:
    def __init__(self, view, service: ActivityServicePort, role: str, *, limit: int = 25) -> None:
        self.view, self.service, self.role = view, service, role
        self.filters: dict[str, object] = {"search": None, "target_audience": None, "season": None, "tag": None, "is_active": None if role == "manager" else True, "limit": limit, "offset": 0}
        self.selected_id: str | None = None; self.selected_activity: dict | None = None; self._loading = False; self._submitting = False
        self.images: list[dict] = []
        self.selected_image_id: str | None = None
        self._preview_generation = 0
        self._preview_cache: OrderedDict[tuple[str, str, str], bytes] = OrderedDict()
        self.view.set_manager_actions(role == "manager")
        self.view.set_media_actions(role == "manager")

    def load(self) -> None:
        if self._loading: return
        self._loading = True; self.view.set_loading(True)
        try:
            payload = self.service.list_activities(dict(self.filters)); items = payload["items"]
            self.view.show_activities([activity_row(x) for x in items], offset=int(self.filters["offset"]), count=len(items), filtered=any(self.filters[k] not in (None, "") for k in ("search", "target_audience", "season", "tag", "is_active")))
            ids = {str(x["id"]) for x in items}
            if self.selected_id in ids: self.view.select_activity(self.selected_id)
            elif self.selected_id is not None: self.selected_id = None; self.selected_activity = None; self._clear_media_selection(); self.view.clear_details()
        except Exception as exc: self._show_error(exc)
        finally: self._loading = False; self.view.set_loading(False)

    def apply_filters(self, values: dict[str, object]) -> None:
        allowed = {"search", "target_audience", "season", "tag"}
        if self.role == "manager": allowed.add("is_active")
        self.filters.update({k: v for k, v in values.items() if k in allowed}); self.filters["offset"] = 0; self.load()

    def page(self, offset: int, limit: int) -> None:
        self.filters.update(offset=max(0, offset), limit=limit); self.load()

    def retry(self) -> None: self.load()

    def select(self, activity_id: str) -> None:
        self.selected_id = activity_id; self.view.set_loading(True)
        try:
            activity = self.service.activity(activity_id); self.selected_activity = activity; self.view.show_details(activity_details(activity), activity)
            self._set_images(list(activity.get("images") or []))
        except ApiError as exc:
            if exc.kind == ApiErrorKind.NOT_FOUND:
                self.selected_id = None; self.selected_activity = None; self._clear_media_selection(); self.view.clear_details(); self.view.show_error("הפעילות שנבחרה אינה קיימת עוד. הרשימה רועננה."); self.load()
            else: self._show_error(exc)
        except Exception as exc: self._show_error(exc)
        finally: self.view.set_loading(False)

    def begin_create(self) -> None:
        if self.role == "manager": self.view.open_activity_form(None, self.submit_create)
    def begin_edit(self) -> None:
        if self.role == "manager" and self.selected_activity: self.view.open_activity_form(self.selected_activity, self.submit_edit)
    def submit_create(self, values, form: FormPort) -> None: self._submit(values, form, None)
    def submit_edit(self, values, form: FormPort) -> None: self._submit(values, form, self.selected_id)

    def _submit(self, values, form: FormPort, activity_id: str | None) -> None:
        if self._submitting or self.role != "manager": return
        try: payload = validate_activity(values)
        except ValueError as exc: form.show_error(str(exc)); return
        self._submitting = True; form.set_submitting(True)
        try:
            activity = self.service.update_activity(activity_id, payload) if activity_id else self.service.create_activity(payload)
            self.selected_id = str(activity["id"]); form.close_success(); self.view.show_success("הפעילות נשמרה בהצלחה."); self.load(); self.select(self.selected_id)
        except Exception as exc:
            form.show_error(self._message(exc))
            if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.CONFLICT and self.selected_id: self.select(self.selected_id)
        finally: self._submitting = False; form.set_submitting(False)

    def deactivate(self) -> None:
        item = self.selected_activity
        if self.role == "manager" and item and item.get("is_active") and self.view.confirm_deactivation(str(item["name"])):
            self._mutate(lambda: self.service.deactivate_activity(str(item["id"])), "הפעילות הושבתה.")
    def reactivate(self) -> None:
        item = self.selected_activity
        if self.role == "manager" and item and not item.get("is_active"):
            self._mutate(lambda: self.service.reactivate_activity(str(item["id"])), "הפעילות הופעלה מחדש.")

    def select_image(self, image_id: str) -> None:
        image = next((item for item in self.images if str(item.get("id")) == image_id), None)
        if image is None or self.selected_id is None:
            return
        self.selected_image_id = image_id
        self.view.select_image(image_id)
        self._load_preview(image)

    def upload_image(self, file_path: str) -> None:
        if self.role != "manager" or self.selected_id is None or self._submitting or not file_path:
            return
        activity_id = self.selected_id
        self._submitting = True
        self.view.set_media_submitting(True)
        try:
            self.service.upload_image(activity_id, file_path)
            self._invalidate_activity_cache(activity_id)
            self.view.show_success("התמונה הועלתה בהצלחה.")
            self.load()
            self.select(activity_id)
        except Exception as exc:
            self._show_error(exc)
        finally:
            self._submitting = False
            self.view.set_media_submitting(False)

    def delete_image(self) -> None:
        if self.role != "manager" or self.selected_id is None or self.selected_image_id is None or self._submitting:
            return
        image = next((item for item in self.images if str(item.get("id")) == self.selected_image_id), None)
        if image is None or not self.view.confirm_image_deletion(str(image.get("original_filename") or "התמונה הנבחרת")):
            return
        activity_id, image_id = self.selected_id, self.selected_image_id
        self._submitting = True
        self.view.set_media_submitting(True)
        try:
            self.service.delete_image(activity_id, image_id)
            self._invalidate_activity_cache(activity_id)
            self.view.show_success("התמונה נמחקה בהצלחה.")
            self.load()
            self.select(activity_id)
        except ApiError as exc:
            if exc.kind == ApiErrorKind.NOT_FOUND:
                self._invalidate_activity_cache(activity_id)
                self.select(activity_id)
            self._show_error(exc)
        except Exception as exc:
            self._show_error(exc)
        finally:
            self._submitting = False
            self.view.set_media_submitting(False)

    def retry_preview(self) -> None:
        if self.selected_image_id:
            image = next((item for item in self.images if str(item.get("id")) == self.selected_image_id), None)
            if image:
                self._load_preview(image, use_cache=False)

    def clear_preview_cache(self) -> None:
        self._preview_cache.clear()
        self._preview_generation += 1

    def _set_images(self, images: list[dict]) -> None:
        self._preview_generation += 1
        self.images = images
        self.view.show_images(images)
        if not images:
            self.selected_image_id = None
            self.view.show_no_images()
            return
        selected = next((item for item in images if item.get("is_primary")), images[0])
        self.selected_image_id = str(selected["id"])
        self.view.select_image(self.selected_image_id)
        self._load_preview(selected)

    def _load_preview(self, image: dict, *, use_cache: bool = True) -> None:
        activity_id = self.selected_id
        image_id = str(image.get("id") or "")
        secure_url = str(image.get("secure_url") or "")
        if not activity_id or not image_id or not secure_url:
            self.view.show_preview_error("לא ניתן להציג את התמונה.")
            return
        self._preview_generation += 1
        generation = self._preview_generation
        key = (activity_id, image_id, secure_url)
        self.view.set_preview_loading(True)
        try:
            data = self._preview_cache.get(key) if use_cache else None
            if data is not None:
                self._preview_cache.move_to_end(key)
            else:
                data = self.service.preview_bytes(secure_url)
            if not self._preview_is_current(generation, activity_id, image_id):
                return
            rendered = self.view.show_preview(data)
            if rendered is not False and key not in self._preview_cache:
                self._preview_cache[key] = data
                self._preview_cache.move_to_end(key)
                while len(self._preview_cache) > MAX_PREVIEW_CACHE_ENTRIES:
                    self._preview_cache.popitem(last=False)
        except Exception:
            if self._preview_is_current(generation, activity_id, image_id):
                self.view.show_preview_error("לא ניתן להציג כרגע את התמונה. נסו שוב.")
        finally:
            if self._preview_is_current(generation, activity_id, image_id):
                self.view.set_preview_loading(False)

    def _preview_is_current(self, generation: int, activity_id: str, image_id: str) -> bool:
        return generation == self._preview_generation and activity_id == self.selected_id and image_id == self.selected_image_id

    def _invalidate_activity_cache(self, activity_id: str) -> None:
        for key in [key for key in self._preview_cache if key[0] == activity_id]:
            self._preview_cache.pop(key, None)
        self._preview_generation += 1

    def _clear_media_selection(self) -> None:
        self._preview_generation += 1
        self.images = []
        self.selected_image_id = None
        self.view.clear_media()

    def _mutate(self, operation: Callable, message: str) -> None:
        if self._submitting: return
        self._submitting = True; self.view.set_loading(True)
        try:
            item = operation(); selected = str(item["id"]); self.selected_id = selected; self.view.show_success(message); self.load()
            if self.selected_id: self.select(selected)
        except Exception as exc: self._show_error(exc)
        finally: self._submitting = False; self.view.set_loading(False)

    def _show_error(self, exc: Exception) -> None:
        if not isinstance(exc, ApiError):
            logger.error("Unexpected activity workflow failure", exc_info=(type(exc), exc, exc.__traceback__))
        self.view.show_error(self._message(exc), retriable=isinstance(exc, ApiError) and exc.retriable, permission=isinstance(exc, ApiError) and exc.kind == ApiErrorKind.PERMISSION)
    @staticmethod
    def _message(exc: Exception) -> str:
        if isinstance(exc, ApiError):
            if exc.kind == ApiErrorKind.PERMISSION: return "אין הרשאה לצפות בפעילות או לשנות אותה."
            if exc.kind == ApiErrorKind.CONFLICT: return "הפעילות השתנתה במקביל. הפרטים רועננו; נסו שוב."
            if exc.kind == ApiErrorKind.CONNECTION: return "לא ניתן להתחבר לשרת. נסו שוב לאחר שהחיבור יחזור."
            if exc.kind == ApiErrorKind.SERVER: return "השרת לא הצליח להשלים את הפעולה. נסו שוב."
        return str(exc) or "הפעולה נכשלה."
