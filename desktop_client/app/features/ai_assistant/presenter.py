from __future__ import annotations

from typing import Protocol

from desktop_client.app.models.operation import OperationExecutor, PresenterOperations


class AIChatView(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def append_message(self, sender: str, message: str) -> None: ...
    def clear_input(self) -> None: ...
    def clear_error(self) -> None: ...


class AIChatPresenter:
    def __init__(self, view: AIChatView, service, executor: OperationExecutor | None = None) -> None:
        self.view = view
        self.service = service
        self._loading = False
        self._operations = PresenterOperations(executor, "ai_chat")

    def invalidate_requests(self) -> None:
        self._operations.invalidate()
        self._loading = False
        self.view.set_loading(False)

    def load(self) -> None:
        return None

    def send_message(self, prompt: str) -> None:
        clean_prompt = prompt.strip()
        if self._loading:
            return
        if not clean_prompt:
            self.view.show_error("יש להזין שאלה לפני השליחה.")
            return

        context = self._operations.begin("consult")
        if context is None:
            return
        self._loading = True
        self.view.set_loading(True)
        self.view.append_message("את/ה", clean_prompt)
        self.view.clear_input()
        def success(response):
            if not self._operations.is_current(context):
                return
            if hasattr(self.view, "clear_error"):
                self.view.clear_error()
            answer = self._format_answer(response)
            self.view.append_message("היועץ", answer or "לא התקבלה תשובה מהשירות.")

        def failure(exc):
            if self._operations.is_current(context):
                self.view.show_error(str(exc))

        def finished():
            if not self._operations.finish(context):
                return
            self._loading = False
            self.view.set_loading(False)

        self._operations.executor.submit(context, lambda: self.service.consult(clean_prompt), success, failure, finished)

    @staticmethod
    def _format_answer(response) -> str:
        if not isinstance(response, dict):
            return str(response or "")
        answer = str(response.get("answer", ""))
        if response.get("answer_basis") not in {"rag", "rag_fallback"}:
            return answer
        sources = response.get("sources")
        if not isinstance(sources, list) or not sources:
            return answer
        source_lines = []
        for source in sources:
            if not isinstance(source, dict):
                continue
            title = str(source.get("source_title", "")).strip()
            uri = str(source.get("source_uri", "") or "").strip()
            if title and uri:
                source_lines.append(f"- {title} ({uri})")
            elif title:
                source_lines.append(f"- {title}")
        if not source_lines:
            return answer
        return f"{answer}\n\nמקורות:\n" + "\n".join(source_lines)
