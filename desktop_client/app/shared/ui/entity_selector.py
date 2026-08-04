from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget


class SearchableEntitySelector(QWidget):
    """Shared RTL selector that displays labels but exposes only real entity IDs."""

    selection_changed = Signal(object)

    def __init__(self, placeholder: str, parent=None) -> None:
        super().__init__(parent); self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(4)
        self.combo = QComboBox(); self.combo.setEditable(True); self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert); self.combo.setPlaceholderText(placeholder)
        self.combo.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive); self.combo.completer().setFilterMode(Qt.MatchFlag.MatchContains); self.combo.lineEdit().setAlignment(Qt.AlignmentFlag.AlignRight)
        self.state = QLabel(); self.state.setAlignment(Qt.AlignmentFlag.AlignRight); self.state.hide(); layout.addWidget(self.combo); layout.addWidget(self.state)
        self.combo.currentIndexChanged.connect(lambda _index: self.selection_changed.emit(self.selected_id()))
        self.combo.lineEdit().textEdited.connect(self._typed)

    def set_items(self, items: list[dict], *, label_key: str, context_keys: tuple[str, ...] = (), active_only: bool = False) -> None:
        selected = self.selected_id(); self.combo.blockSignals(True); self.combo.clear(); self.combo.addItem("— יש לבחור —", None)
        for item in items:
            if active_only and not item.get("is_active", True): continue
            primary = str(item.get(label_key) or item.get("id")); context = [str(item.get(key)) for key in context_keys if item.get(key)]
            self.combo.addItem(primary + (" · " + " · ".join(context) if context else ""), str(item["id"])); self.combo.setItemData(self.combo.count()-1, item, int(Qt.ItemDataRole.UserRole)+1)
        index = self.combo.findData(selected); self.combo.setCurrentIndex(index if index >= 0 else 0); self.combo.blockSignals(False); self.show_empty(self.combo.count() == 1)

    def selected_id(self) -> str | None:
        index = self.combo.currentIndex()
        if index <= 0: return None
        if self.combo.currentText() != self.combo.itemText(index): return None
        value = self.combo.itemData(index); return str(value) if value is not None else None

    def selected_entity(self) -> dict | None:
        index = self.combo.currentIndex(); return self.combo.itemData(index, int(Qt.ItemDataRole.UserRole)+1) if index > 0 and self.selected_id() else None

    def select_id(self, entity_id: str | None) -> None:
        index = self.combo.findData(str(entity_id)) if entity_id else 0; self.combo.setCurrentIndex(index if index >= 0 else 0)

    def clear_selection(self) -> None: self.combo.setCurrentIndex(0)
    def set_loading(self, loading: bool) -> None: self.combo.setEnabled(not loading); self.state.setText("טוען אפשרויות…"); self.state.setVisible(loading)
    def show_empty(self, empty: bool) -> None:
        if empty: self.state.setText("לא נמצאו אפשרויות זמינות.")
        self.state.setVisible(empty)
    def show_error(self, message: str) -> None: self.state.setText(message); self.state.setProperty("feedback", "error"); self.state.show()
    def _typed(self, text: str) -> None:
        exact = self.combo.findText(text, Qt.MatchFlag.MatchFixedString)
        if exact < 0: self.combo.setCurrentIndex(-1)
        self.selection_changed.emit(self.selected_id())
