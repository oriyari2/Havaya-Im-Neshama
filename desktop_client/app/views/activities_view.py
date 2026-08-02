from __future__ import annotations

from PySide6.QtCore import QEvent, QItemSelectionModel, Qt, Signal
from PySide6.QtGui import QKeyEvent, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QTableWidgetItem, QVBoxLayout, QWidget,
)

from desktop_client.app.models.request_state import RequestPhase, RequestState
from desktop_client.app.views.activity_dialogs import ActivityDialog
from desktop_client.app.views.common import StatefulWidget
from desktop_client.app.views.design_tokens import SPACE_2, SPACE_3, SPACE_4
from desktop_client.app.views.filter_popup import FloatingFilterPopup
from desktop_client.app.views.management_common import ActiveBadge, RetryState, confirm_action
from desktop_client.app.views.management_workspace import ManagementWorkspace
from desktop_client.app.views.ui_foundations import ColumnKind, ColumnPolicy, set_disabled_explanation, set_item_text


def _positive_integer(value) -> int | None:
    if isinstance(value, bool): return None
    try: number = int(value)
    except (TypeError, ValueError, OverflowError): return None
    return number if number >= 0 else None


def _image_label(image: dict) -> str:
    raw_name = image.get("original_filename")
    name = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else "תמונה ללא שם"
    width, height = _positive_integer(image.get("width")), _positive_integer(image.get("height"))
    dimensions = f"{width}×{height}" if width is not None and height is not None else "ממדים לא זמינים"
    byte_count = _positive_integer(image.get("bytes"))
    size = f"{byte_count // 1024} KiB" if byte_count is not None else "גודל לא זמין"
    return " • ".join((name, dimensions, size)) + (" • ראשית" if image.get("is_primary") else "")


class ActivitiesView(StatefulWidget):
    filters_requested = Signal(dict); page_requested = Signal(int, int); activity_selected = Signal(str); retry_requested = Signal()
    create_requested = Signal(); edit_requested = Signal(); deactivate_requested = Signal(); reactivate_requested = Signal()
    image_selected = Signal(str); upload_image_requested = Signal(str); delete_image_requested = Signal(); preview_retry_requested = Signal()

    def __init__(self, role: str) -> None:
        super().__init__(); self.role = role; self._selected_id = None; self._pending_open_id = None; self._empty_filtered = False; self._source_pixmap = QPixmap()
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0)
        headers = ("שם פעילות", "קהל יעד", "עונה", "משך", "תמחור") + (("מצב",) if role == "manager" else ())
        policies = (
            ColumnPolicy(ColumnKind.PRIMARY_TEXT, 220), ColumnPolicy(ColumnKind.SECONDARY_TEXT, 170, 250),
            ColumnPolicy(ColumnKind.SECONDARY_TEXT, 130, 190), ColumnPolicy(ColumnKind.COMPACT, 110),
            ColumnPolicy(ColumnKind.SECONDARY_TEXT, 180, 280),
        ) + ((ColumnPolicy(ColumnKind.COMPACT, 110),) if role == "manager" else ())
        self.workspace = ManagementWorkspace(
            title="פעילויות" if role == "manager" else "קטלוג פעילויות",
            subtitle="ניהול פעילויות, קהלי יעד ותמחור" if role == "manager" else "עיון בפעילויות הזמינות",
            create_text="פעילות חדשה", plural="פעילויות",
            detail_subtitle="מידע מלא ופעולות עבור הפעילות שנבחרה",
            search_placeholder="חיפוש לפי שם או תיאור", sort_options=(("name", "מיון לפי: שם"), ("duration_minutes", "מיון לפי: משך פעילות")),
            headers=headers, policies=policies,
        )
        root.addWidget(self.workspace)
        for name in ("scaffold", "toolbar", "table", "footer", "create_button", "pages", "list_page", "details_page", "back_button"):
            setattr(self, name, getattr(self.workspace, name))
        self.retry_state = RetryState(); self.retry_state.hide(); self.retry_state.retry_requested.connect(self.retry_requested); self.scaffold.main_content.insertWidget(0, self.retry_state)
        self.actions = self.workspace.actions_container
        self.create_button.setVisible(role == "manager")

        self.filter_button = QPushButton("סינון", self.toolbar); self.filter_button.hide()
        self.filter_popup = FloatingFilterPopup(self.filter_button, self.list_page)
        self.audience = QComboBox(); self.audience.setEditable(True); self.audience.addItem("כל קהלי היעד", "")
        self.season = QComboBox(); self.season.setEditable(True); self.season.addItem("כל העונות", "")
        self.active = QComboBox(); self.active.addItem("כל המצבים", None); self.active.addItem("פעילה", True); self.active.addItem("לא פעילה", False); self.active.setVisible(role == "manager")
        self.filter_popup.add_section("קהל יעד", self.audience); self.filter_popup.add_section("עונה", self.season)
        if role == "manager": self.filter_popup.add_section("מצב", self.active)
        self.apply_filters_button = self.filter_popup.apply_button; self.clear_filters_button = self.filter_popup.clear_button

        self.edit_button = self.workspace.add_action("עריכת פעילות")
        self.deactivate_button = self.workspace.add_action("השבתת פעילות", destructive=True)
        self.reactivate_button = self.workspace.add_action("הפעלת פעילות מחדש")
        self.activity_details = self.workspace.add_card("פרטי פעילות")
        self.operational_details = self.workspace.add_card("תפעול ותמחור")
        self.system_details = self.workspace.add_card("מידע מערכת")
        self._build_gallery()

        self.create_button.clicked.connect(self.create_requested); self.edit_button.clicked.connect(self.edit_requested)
        self.deactivate_button.clicked.connect(self.deactivate_requested); self.reactivate_button.clicked.connect(self.reactivate_requested)
        self.toolbar.search_requested.connect(lambda search, order: self.filters_requested.emit({"search": search or None, "order_by": order or "name"}))
        self.toolbar.sort_combo.currentIndexChanged.connect(lambda _index: self.filters_requested.emit({"search": self.toolbar.search_input.text().strip() or None, "order_by": str(self.toolbar.sort_combo.currentData() or "name")}))
        self.toolbar.refresh_requested.connect(self._reset_filters)
        self.filter_button.clicked.connect(self.filter_popup.toggle); self.filter_popup.apply_requested.connect(self._apply_filters); self.filter_popup.clear_requested.connect(self._clear_popup_filters); self.footer.page_requested.connect(self.page_requested)
        self.table.itemSelectionChanged.connect(self._select); self.table.cellDoubleClicked.connect(lambda row, _column: self._request_open(self._row_id(row))); self.table.installEventFilter(self)
        self.workspace.empty_action_button.clicked.connect(self._empty_action); self.clear_details()
        self.set_manager_actions(role == "manager"); self.set_media_actions(role == "manager")

    def _build_gallery(self) -> None:
        self.media_group = QFrame(); self.media_group.setObjectName("detailPanel")
        media = QVBoxLayout(self.media_group); media.setContentsMargins(SPACE_4, SPACE_4, SPACE_4, SPACE_4); media.setSpacing(SPACE_3)
        heading_row = QHBoxLayout(); heading_row.setContentsMargins(0, 0, 0, 0); heading_row.addStretch()
        self.gallery_heading = QLabel("גלריית תמונות"); self.gallery_heading.setObjectName("sectionTitle"); self.gallery_heading.setLayoutDirection(Qt.LayoutDirection.RightToLeft); self.gallery_heading.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute); heading_row.addWidget(self.gallery_heading); media.addLayout(heading_row)
        self.preview = QLabel("אין תמונות להצגה."); self.preview.setObjectName("activityImagePreview"); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.preview.setMinimumHeight(260); self.preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.preview.setWordWrap(True); media.addWidget(self.preview, 1)
        nav = QHBoxLayout(); nav.setDirection(QHBoxLayout.Direction.RightToLeft); self.previous_image_button = QPushButton("הקודמת"); self.next_image_button = QPushButton("הבאה"); self.image_position = QLabel("0 מתוך 0"); self.image_position.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.addWidget(self.previous_image_button); nav.addWidget(self.image_position); nav.addWidget(self.next_image_button); nav.addStretch(); media.addLayout(nav)
        self.image_list = QListWidget(); self.image_list.setLayoutDirection(Qt.LayoutDirection.RightToLeft); self.image_list.setMaximumHeight(90); self.image_list.currentItemChanged.connect(self._image_changed); media.addWidget(self.image_list)
        self.preview_retry = QPushButton("נסו שוב להציג תמונה"); self.preview_retry.clicked.connect(self.preview_retry_requested); self.preview_retry.hide(); media.addWidget(self.preview_retry)
        self.media_actions = QWidget(); actions = QHBoxLayout(self.media_actions); actions.setDirection(QHBoxLayout.Direction.RightToLeft); actions.setContentsMargins(0, 0, 0, 0)
        self.upload_image_button = QPushButton("העלאת תמונה"); self.delete_image_button = QPushButton("הסרת התמונה הנוכחית"); actions.addWidget(self.upload_image_button); actions.addWidget(self.delete_image_button); actions.addStretch(); media.addWidget(self.media_actions)
        self.upload_image_button.clicked.connect(self._choose_image); self.delete_image_button.clicked.connect(self.delete_image_requested)
        self.previous_image_button.clicked.connect(lambda: self._move_image(-1)); self.next_image_button.clicked.connect(lambda: self._move_image(1))
        self.preview.installEventFilter(self); self.preview.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.media_actions.setVisible(self.role == "manager")
        body = self.workspace.details_widget.layout(); body.insertWidget(body.count() - 1, self.media_group)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.table and event.type() == QEvent.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter): self._open(); return True
        if watched is self.preview and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Left: self._move_image(1); return True
            if event.key() == Qt.Key.Key_Right: self._move_image(-1); return True
        return super().eventFilter(watched, event)

    def _row_id(self, row: int) -> str: return str(self.table.item(row, 1).data(Qt.ItemDataRole.UserRole))
    def _select(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows: self._selected_id = None; return
        activity_id = self._row_id(rows[0].row()); changed = activity_id != self._selected_id; self._selected_id = activity_id
        if changed: self._clear_forms(); self.workspace.detail_title.clear(); self.workspace.show_list(); self.activity_selected.emit(activity_id)
    def _open(self) -> None:
        if self._selected_id: self._pending_open_id = self._selected_id
        if self._selected_id and self.workspace.detail_title.text(): self._pending_open_id = None; self.workspace.show_details()
    def _request_open(self, activity_id: str) -> None:
        self._pending_open_id = activity_id; self.select_activity(activity_id)
        if self.workspace.detail_title.text() and self._selected_id == activity_id: self._pending_open_id = None; self.workspace.show_details()

    def _apply_filters(self) -> None:
        self.filter_popup.hide()
        audience = self.audience.currentText().strip(); season = self.season.currentText().strip()
        values = {"target_audience": None if audience == "כל קהלי היעד" else audience or None, "season": None if season == "כל העונות" else season or None}
        if self.role == "manager": values["is_active"] = self.active.currentData()
        self.filters_requested.emit(values)
    def _clear_popup_filters(self) -> None:
        self.audience.setCurrentIndex(0); self.audience.setEditText("כל קהלי היעד"); self.season.setCurrentIndex(0); self.season.setEditText("כל העונות"); self.active.setCurrentIndex(0); self._apply_filters()
    def _reset_filters(self) -> None:
        self._reset_controls()
        values = {"search": None, "target_audience": None, "season": None, "tag": None, "order_by": "name", "_clear_selection": True}
        if self.role == "manager": values["is_active"] = None
        self.filters_requested.emit(values)
    def _reset_controls(self) -> None:
        self.toolbar.search_input.clear(); blocked = self.toolbar.sort_combo.blockSignals(True); self.toolbar.sort_combo.setCurrentIndex(0); self.toolbar.sort_combo.blockSignals(blocked); self.audience.setCurrentIndex(0); self.audience.setEditText("כל קהלי היעד"); self.season.setCurrentIndex(0); self.season.setEditText("כל העונות"); self.active.setCurrentIndex(0); self.filter_popup.hide(); self.table.clearSelection(); self.clear_details()
    def _empty_action(self) -> None: self._reset_filters() if self._empty_filtered else self.create_requested.emit()

    def set_manager_actions(self, manager: bool) -> None: self.create_button.setVisible(manager); self.actions.setVisible(manager)
    def set_media_actions(self, manager: bool) -> None: self.media_actions.setVisible(manager)
    def set_loading(self, value: bool) -> None:
        self.create_button.setEnabled(not value); self.toolbar.setEnabled(not value); self.footer.setEnabled(not value)
        if value and not self.table.rowCount(): self.workspace.show_loading("טוען פעילויות…")
    def show_error(self, message: str, *, retriable=False, permission=False) -> None:
        self.retry_state.show_message(message, retriable=retriable)
    def show_success(self, message: str) -> None: self.scaffold.feedback.render(RequestState(RequestPhase.SUCCESS, message, "activities"))

    def show_activities(self, rows, *, offset, count, filtered) -> None:
        self.retry_state.hide(); self.table.setRowCount(len(rows)); keys = ("name", "target_audience", "season", "duration_minutes", "pricing_rule")
        for row_index, row in enumerate(rows):
            self.workspace.set_row_open_action(row_index, str(row["id"]), self._request_open)
            for column, key in enumerate(keys, start=1):
                value = row.get(key) or "—"; value = f"{value} דקות" if key == "duration_minutes" and value != "—" else value
                item = QTableWidgetItem(str(value)); item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute); set_item_text(self.table, row_index, column, item, tooltip_direction=Qt.LayoutDirection.RightToLeft)
                if column == 1: item.setData(Qt.ItemDataRole.UserRole, str(row["id"]))
            if self.role == "manager": badge = ActiveBadge(); badge.set_active(bool(row.get("is_active"))); self.workspace.configure_status_badge(badge); self.table.setCellWidget(row_index, 6, badge)
        self.footer.set_page(offset=offset, count=count); self.workspace.results_label.setText(f"פעילויות • {len(rows)}"); self._empty_filtered = filtered; self.workspace.show_empty_state(empty=not rows, filtered=filtered, plural="פעילויות"); self.footer.setVisible(bool(rows))

    def show_details(self, details, activity) -> None:
        self._selected_id = str(activity.get("id") or self._selected_id); self._clear_forms()
        activity_labels = {"שם", "תיאור", "קהל יעד", "עונה", "תגיות"}; system_labels = {"מצב", "נוצרה", "עודכנה"}
        for label, value in details:
            content = QLabel(value); content.setWordWrap(True); content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); content.setToolTip(value)
            target = self.activity_details if label in activity_labels else self.system_details if label in system_labels else self.operational_details
            self.workspace.add_property_row(target, label, content)
        active = bool(activity.get("is_active")); self.workspace.show_detail_identity(str(activity.get("name") or "פרטי פעילות"), active); self.workspace.detail_subtitle.setText(str(activity.get("description") or "מידע מלא ופעולות עבור הפעילות שנבחרה")); self.workspace.set_actions_enabled(self.role == "manager")
        self.deactivate_button.setVisible(self.role == "manager" and active); self.reactivate_button.setVisible(self.role == "manager" and not active); self.edit_button.setVisible(self.role == "manager")
        if self._pending_open_id == str(activity.get("id")): self._pending_open_id = None; self.workspace.show_details()
    def _clear_forms(self) -> None:
        for form in (self.activity_details, self.operational_details, self.system_details):
            while form.rowCount(): form.removeRow(0)
    def clear_details(self) -> None:
        if hasattr(self, "activity_details"): self._clear_forms(); self.workspace.detail_title.clear(); self.workspace.set_actions_enabled(False); self.workspace.show_list()
        self._selected_id = None; self._pending_open_id = None; self.deactivate_button.hide(); self.reactivate_button.hide(); self.clear_media()
        for button in (self.edit_button, self.deactivate_button, self.reactivate_button): set_disabled_explanation(button, "יש לבחור פעילות תחילה")
    def reset_to_default(self) -> None:
        dialog = getattr(self, "_dialog", None)
        if dialog is not None and dialog.isVisible(): dialog.reject()
        self._reset_controls(); self.scaffold.feedback.hide()
    def select_activity(self, activity_id: str) -> None:
        for row in range(self.table.rowCount()):
            if self._row_id(row) == activity_id:
                changed = self._selected_id != activity_id; blocked = self.table.blockSignals(True); index = self.table.model().index(row, 1); self.table.selectionModel().setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows); self.table.blockSignals(blocked); self._selected_id = activity_id
                if changed: self._clear_forms(); self.workspace.detail_title.clear(); self.workspace.show_list(); self.activity_selected.emit(activity_id)
                break
    def open_activity_form(self, initial, submit) -> None: self._dialog = ActivityDialog(initial, self); self._dialog.submitted.connect(submit); self._dialog.open()
    def confirm_deactivation(self, name: str) -> bool: return confirm_action(self, "אישור השבתה", f"להשבית את הפעילות {name}? הפעילות תישמר במערכת ותוכל להיות מופעלת מחדש.")

    def show_images(self, images) -> None:
        self.image_list.blockSignals(True); self.image_list.clear()
        for image in images:
            item = QListWidgetItem(_image_label(image)); item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignAbsolute); item.setData(Qt.ItemDataRole.UserRole, str(image.get("id"))); self.image_list.addItem(item)
        self.image_list.blockSignals(False); self.delete_image_button.setEnabled(False); self._update_gallery_controls()
    def select_image(self, image_id: str) -> None:
        self.image_list.blockSignals(True)
        for index in range(self.image_list.count()):
            item = self.image_list.item(index)
            if str(item.data(Qt.ItemDataRole.UserRole)) == image_id: self.image_list.setCurrentItem(item); break
        self.image_list.blockSignals(False); self.delete_image_button.setEnabled(self.role == "manager"); self._update_gallery_controls()
    def _image_changed(self, current, _previous) -> None:
        self._update_gallery_controls()
        if current is not None: self.image_selected.emit(str(current.data(Qt.ItemDataRole.UserRole)))
    def _move_image(self, delta: int) -> None:
        count = self.image_list.count()
        if not count: return
        current = self.image_list.currentRow(); self.image_list.setCurrentRow((max(0, current) + delta) % count)
    def _update_gallery_controls(self) -> None:
        count = self.image_list.count(); row = self.image_list.currentRow(); self.image_position.setText(f"{row + 1 if row >= 0 else 0} מתוך {count}"); enabled = count > 1; self.previous_image_button.setEnabled(enabled); self.next_image_button.setEnabled(enabled)
    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "בחירת תמונה", "", "תמונות (*.jpg *.jpeg *.png *.webp)")
        if path: self.upload_image_requested.emit(path)
    def set_media_submitting(self, submitting: bool) -> None: self.upload_image_button.setEnabled(not submitting); self.delete_image_button.setEnabled(not submitting and self.role == "manager" and self.image_list.currentItem() is not None)
    def set_preview_loading(self, loading: bool) -> None:
        if loading: self._source_pixmap = QPixmap(); self.preview.clear(); self.preview.setText("טוען תמונה…"); self.preview_retry.hide()
    def show_preview(self, data: bytes) -> bool:
        pixmap = QPixmap(); valid = pixmap.loadFromData(data)
        if not valid: self.show_preview_error("לא ניתן לפענח את קובץ התמונה."); return False
        self._source_pixmap = pixmap; self._render_pixmap(); self.preview_retry.hide(); return True
    def _render_pixmap(self) -> None:
        if not self._source_pixmap.isNull(): self.preview.setText(""); self.preview.setPixmap(self._source_pixmap.scaled(self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event); self._render_pixmap()
    def show_preview_error(self, message: str) -> None: self._source_pixmap = QPixmap(); self.preview.clear(); self.preview.setText(message); self.preview_retry.show()
    def show_no_images(self) -> None: self._source_pixmap = QPixmap(); self.preview.clear(); self.preview.setText("אין תמונות להצגה."); self.preview_retry.hide(); self.delete_image_button.setEnabled(False); self._update_gallery_controls()
    def clear_media(self) -> None: self.image_list.clear(); self.show_no_images()
    def confirm_image_deletion(self, name: str) -> bool: return confirm_action(self, "אישור הסרת תמונה", f"להסיר את {name}? הקובץ יימחק גם משירות התמונות.")
