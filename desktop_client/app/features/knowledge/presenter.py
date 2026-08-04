from __future__ import annotations

from typing import Protocol

from desktop_client.app.models.operation import OperationExecutor, PresenterOperations


class KnowledgeView(Protocol):
    def show_sources(self, sources: list[dict]) -> None: ...
    def show_source_detail(self, source: dict) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_message(self, message: str) -> None: ...
    def reset_editor(self) -> None: ...


class KnowledgeManagementPresenter:
    def __init__(self, view: KnowledgeView, service, executor: OperationExecutor | None = None) -> None:
        self.view, self.service = view, service
        self._operations = PresenterOperations(executor, "knowledge")
        self._submitting = False

    def invalidate_requests(self) -> None:
        self._operations.invalidate()

    def load(self) -> None:
        context = self._operations.replace("list")
        self._operations.executor.submit(
            context,
            self.service.list_sources,
            lambda sources: self.view.show_sources(sources) if self._operations.is_current(context) else None,
            lambda exc: self.view.show_error(str(exc)) if self._operations.is_current(context) else None,
            lambda: self._operations.finish(context),
        )

    def retry(self) -> None:
        invalidate = getattr(self.service, "invalidate_list", None)
        if invalidate is not None:
            invalidate()
        self.load()

    def select_source(self, source_id: str) -> None:
        context = self._operations.replace("detail")
        self._operations.executor.submit(
            context,
            lambda: self.service.get_source(source_id),
            lambda source: self.view.show_source_detail(source) if self._operations.is_current(context) else None,
            lambda exc: self.view.show_error(str(exc)) if self._operations.is_current(context) else None,
            lambda: self._operations.finish(context),
        )

    def save(self, values: dict) -> None:
        self._mutate(lambda: self._write_new(values), "מקור הידע נשמר.")

    def replace(self, source_id: str, values: dict) -> None:
        def operation():
            file_path = values.get("file_path")
            if file_path:
                return self.service.replace_with_file(
                    source_id,
                    title=str(values.get("title", "")),
                    category=str(values.get("category", "")),
                    activity_name=values.get("activity_name"),
                    allowed_roles=list(values.get("allowed_roles", [])),
                    path=str(file_path),
                )
            return self.service.replace_source(source_id, self._payload_from_values(values))

        self._mutate(operation, "מקור הידע הוחלף.")

    def delete(self, source_id: str) -> None:
        self._mutate(lambda: self.service.delete_source(source_id), "מקור הידע נמחק.")

    def _mutate(self, operation, message: str) -> None:
        if self._submitting:
            return
        context = self._operations.begin("mutation")
        if context is None:
            return
        self._submitting = True

        def success(_result):
            if not self._operations.is_current(context):
                return
            self.view.reset_editor()
            self.view.show_message(message)
            self.load()

        def failure(_exc):
            if self._operations.is_current(context):
                self.view.show_error("לא ניתן להשלים את פעולת מקור הידע. נסו שוב.")

        def finished():
            if self._operations.finish(context):
                self._submitting = False

        self._operations.executor.submit(context, operation, success, failure, finished)

    def _write_new(self, values: dict):
        file_path = values.get("file_path")
        if file_path:
            return self.service.upload_source(
                title=str(values.get("title", "")),
                category=str(values.get("category", "")),
                activity_name=values.get("activity_name"),
                allowed_roles=list(values.get("allowed_roles", [])),
                path=str(file_path),
            )
        return self.service.create_text_source(self._payload_from_values(values))

    @staticmethod
    def _payload_from_values(values: dict) -> dict:
        return {
            "title": str(values.get("title", "")),
            "category": str(values.get("category", "")),
            "activity_name": values.get("activity_name"),
            "allowed_roles": list(values.get("allowed_roles", [])),
            "content": str(values.get("content", "")),
        }
