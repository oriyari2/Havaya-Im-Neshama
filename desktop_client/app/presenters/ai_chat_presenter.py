from __future__ import annotations

from typing import Protocol


class AIChatView(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def append_message(self, sender: str, message: str) -> None: ...
    def clear_input(self) -> None: ...


class AIChatPresenter:
    def __init__(self, view: AIChatView, service) -> None:
        self.view = view
        self.service = service
        self._loading = False

    def load(self) -> None:
        return None

    def send_message(self, prompt: str) -> None:
        clean_prompt = prompt.strip()
        if self._loading:
            return
        if not clean_prompt:
            self.view.show_error("יש להזין שאלה לפני השליחה.")
            return

        self._loading = True
        self.view.set_loading(True)
        self.view.append_message("את/ה", clean_prompt)
        self.view.clear_input()
        try:
            answer = self.service.consult(clean_prompt)
            self.view.append_message("היועץ", answer or "לא התקבלה תשובה מהשירות.")
        except Exception as exc:
            self.view.show_error(str(exc))
        finally:
            self._loading = False
            self.view.set_loading(False)
