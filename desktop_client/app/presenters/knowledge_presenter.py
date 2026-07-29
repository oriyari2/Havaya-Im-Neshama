from __future__ import annotations

from typing import Protocol


class KnowledgeView(Protocol):
    def show_sources(self, sources: list[dict]) -> None: ...
    def show_source_detail(self, source: dict) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_message(self, message: str) -> None: ...
    def clear_file_path(self) -> None: ...


class KnowledgeManagementPresenter:
    def __init__(self, view: KnowledgeView, service) -> None:
        self.view = view
        self.service = service

    def load(self) -> None:
        try:
            self.view.show_sources(self.service.list_sources())
        except Exception as exc:
            self.view.show_error(str(exc))

    def select_source(self, source_id: str) -> None:
        try:
            self.view.show_source_detail(self.service.get_source(source_id))
        except Exception as exc:
            self.view.show_error(str(exc))

    def save(self, values: dict) -> None:
        try:
            self._write_new(values)
            self.view.clear_file_path()
            self.view.show_message("מקור הידע נשמר.")
            self.load()
        except Exception as exc:
            self.view.show_error(str(exc))

    def replace(self, source_id: str, values: dict) -> None:
        try:
            file_path = values.get("file_path")
            if file_path:
                self.service.replace_with_file(
                    source_id,
                    title=str(values.get("title", "")),
                    category=str(values.get("category", "")),
                    activity_name=values.get("activity_name"),
                    allowed_roles=list(values.get("allowed_roles", [])),
                    path=str(file_path),
                )
            else:
                self.service.replace_source(source_id, self._payload_from_values(values))
            self.view.clear_file_path()
            self.view.show_message("מקור הידע הוחלף.")
            self.load()
        except Exception as exc:
            self.view.show_error(str(exc))

    def delete(self, source_id: str) -> None:
        try:
            self.service.delete_source(source_id)
            self.view.show_message("מקור הידע נמחק.")
            self.load()
        except Exception as exc:
            self.view.show_error(str(exc))

    def _write_new(self, values: dict) -> None:
        file_path = values.get("file_path")
        if file_path:
            self.service.upload_source(
                title=str(values.get("title", "")),
                category=str(values.get("category", "")),
                activity_name=values.get("activity_name"),
                allowed_roles=list(values.get("allowed_roles", [])),
                path=str(file_path),
            )
            return
        self.service.create_text_source(self._payload_from_values(values))

    @staticmethod
    def _payload_from_values(values: dict) -> dict:
        return {
            "title": str(values.get("title", "")),
            "category": str(values.get("category", "")),
            "activity_name": values.get("activity_name"),
            "allowed_roles": list(values.get("allowed_roles", [])),
            "content": str(values.get("content", "")),
        }
