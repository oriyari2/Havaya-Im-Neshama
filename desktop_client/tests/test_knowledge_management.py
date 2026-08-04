from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from desktop_client.app.main import MainWindow
from desktop_client.app.models.session import Session
from desktop_client.app.features.knowledge.presenter import KnowledgeManagementPresenter
from desktop_client.app.features.knowledge.service import MAX_KNOWLEDGE_SOURCE_CONTENT_CHARS, KnowledgeService, read_supported_knowledge_file
from desktop_client.app.features.knowledge.view import KnowledgeManagementView


class KnowledgeDesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_manager_only_navigation_contains_knowledge_screen(self) -> None:
        class Api:
            def set_unauthorized_handler(self, handler):
                self.handler = handler

            def set_access_token(self, token):
                pass

        class Service:
            def dashboard(self):
                return {}

            def list_bookings(self, filters=None):
                return {"items": [], "count": 0}

            def list_customers(self, filters=None):
                return {"items": [], "count": 0}

            def list_activities(self, filters=None):
                return {"items": [], "count": 0}

            def list_instructors(self, filters=None):
                return {"items": [], "count": 0}

            def open_events(self):
                return []

        for role in ("manager", "instructor", "customer"):
            window = MainWindow(Api())
            window.booking_service = Service()
            window.customer_service = Service()
            window.activity_service = Service()
            window.instructor_service = Service()
            window.knowledge_service = Service()
            window._show_workspace(Session("token", "id", f"{role}@example.com", role))
            self.assertEqual("knowledge" in window.shell.pages, role == "manager")
            self.assertEqual("knowledge" in window.shell.navigation_buttons, role == "manager")
            window.close()

    def test_view_values_include_selected_visibility(self) -> None:
        view = KnowledgeManagementView()
        view.title_input.setText("Guide")
        view.category_input.setText("equipment")
        view.content_input.setPlainText("approved text")
        view.instructor_checkbox.setChecked(True)

        values = view.values()

        self.assertEqual(values["allowed_roles"], ["instructor"])
        self.assertEqual(values["content"], "approved text")


    def test_required_fields_are_marked_and_editor_resets_after_success(self) -> None:
        view = KnowledgeManagementView()
        self.addCleanup(view.close)
        labels = [label.text() for label in view.findChildren(type(view.required_hint))]

        self.assertIn("* שדה חובה", view.required_hint.text())
        self.assertIn("כותרת *", labels)
        self.assertIn("קטגוריה *", labels)
        self.assertIn("תוכן או קובץ *", labels)

        view.title_input.setText("Guide")
        view.category_input.setText("general")
        view.activity_input.setText("Activity")
        view.content_input.setPlainText("content")
        view.file_path_input.setText("guide.md")
        view.instructor_checkbox.setChecked(True)
        view.customer_checkbox.setChecked(True)
        view.show_source_detail({
            "source_id": "source-1",
            "title": "Guide",
            "category": "general",
            "activity_name": "Activity",
            "content": "content",
            "allowed_roles": ["instructor", "customer"],
        })

        view.reset_editor()

        self.assertEqual(view.values(), {
            "title": "",
            "category": "",
            "activity_name": None,
            "content": "",
            "file_path": None,
            "allowed_roles": [],
        })
        self.assertIsNone(view._selected_source_id)
        self.assertFalse(view.replace_button.isEnabled())
        self.assertFalse(view.delete_button.isEnabled())
        self.assertTrue(view.save_button.isEnabled())

    def test_presenter_uses_pasted_text_and_refreshes(self) -> None:
        view = _View()
        service = _Service()
        presenter = KnowledgeManagementPresenter(view, service)

        presenter.save({"title": "Guide", "category": "general", "content": "text", "allowed_roles": ["customer"]})

        self.assertEqual(service.created["content"], "text")
        self.assertTrue(view.sources_shown)

    def test_service_upload_reads_txt_or_md_through_backend_api(self) -> None:
        api = _Api()
        service = KnowledgeService(api)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "guide.md"
            path.write_text("file text", encoding="utf-8")

            service.upload_source(title="Guide", category="general", activity_name=None, allowed_roles=["customer"], path=str(path))

        self.assertEqual(api.last_post[0], "/api/rag/sources")
        self.assertEqual(api.last_post[1]["source_uri"], "guide.md")
        self.assertEqual(api.last_post[1]["content"], "file text")

    def test_service_rejects_decoded_text_over_shared_character_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            accepted = Path(directory) / "accepted.md"
            accepted.write_text("a" * MAX_KNOWLEDGE_SOURCE_CONTENT_CHARS, encoding="utf-8")
            rejected = Path(directory) / "rejected.md"
            rejected.write_text("a" * (MAX_KNOWLEDGE_SOURCE_CONTENT_CHARS + 1), encoding="utf-8")

            _, content = read_supported_knowledge_file(str(accepted))
            with self.assertRaisesRegex(ValueError, "50,000 characters"):
                read_supported_knowledge_file(str(rejected))

        self.assertEqual(len(content), MAX_KNOWLEDGE_SOURCE_CONTENT_CHARS)

    def test_presenter_replace_uses_selected_file_content(self) -> None:
        view = _View()
        service = _Service()
        presenter = KnowledgeManagementPresenter(view, service)

        presenter.replace(
            "source-1",
            {
                "title": "Guide",
                "category": "general",
                "content": "ignored pasted text",
                "file_path": "replacement.md",
                "allowed_roles": ["customer"],
            },
        )

        self.assertEqual(service.replaced_file["source_id"], "source-1")
        self.assertEqual(service.replaced_file["path"], "replacement.md")
        self.assertEqual(service.replaced_file["allowed_roles"], ["customer"])
        self.assertTrue(view.sources_shown)

    def test_view_clears_selected_file_when_source_or_text_changes(self) -> None:
        view = KnowledgeManagementView()
        view.file_path_input.setText("stale.md")

        view.show_source_detail(
            {
                "source_id": "source-1",
                "title": "Guide",
                "category": "general",
                "content": "loaded text",
                "allowed_roles": ["customer"],
            }
        )

        self.assertEqual(view.file_path_input.text(), "")
        view.file_path_input.setText("replacement.md")
        view.content_input.setPlainText("pasted replacement")
        self.assertEqual(view.file_path_input.text(), "")

    def test_presenter_resets_editor_after_successful_create_or_replace(self) -> None:
        view = _View()
        service = _Service()
        presenter = KnowledgeManagementPresenter(view, service)

        presenter.save({"title": "Guide", "category": "general", "content": "text", "allowed_roles": []})
        presenter.replace("source-1", {"title": "Guide", "category": "general", "content": "text", "allowed_roles": []})

        self.assertEqual(view.reset_editor_count, 2)

    def test_presenter_resets_editor_after_successful_delete(self) -> None:
        view = _View()
        service = _Service()
        presenter = KnowledgeManagementPresenter(view, service)

        presenter.delete("source-1")

        self.assertEqual(service.deleted, "source-1")
        self.assertEqual(view.reset_editor_count, 1)
        self.assertEqual(view.message, "מקור הידע נמחק.")
        self.assertTrue(view.sources_shown)

    def test_pasted_replacement_is_not_overridden_by_stale_selected_file(self) -> None:
        view = KnowledgeManagementView()
        service = _Service()
        presenter = KnowledgeManagementPresenter(view, service)
        view.show_source_detail(
            {
                "source_id": "source-1",
                "title": "Guide",
                "category": "general",
                "content": "loaded text",
                "allowed_roles": ["customer"],
            }
        )
        view.file_path_input.setText("stale.md")
        view.content_input.setPlainText("new pasted replacement")

        presenter.replace("source-1", view.values())

        self.assertEqual(service.replaced["content"], "new pasted replacement")
        self.assertFalse(hasattr(service, "replaced_file"))

    def test_service_replace_with_file_reads_content_and_filename(self) -> None:
        api = _Api()
        service = KnowledgeService(api)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "replacement.txt"
            path.write_text("replacement file text", encoding="utf-8")

            service.replace_with_file(
                "source-1",
                title="Guide",
                category="general",
                activity_name=None,
                allowed_roles=["instructor"],
                path=str(path),
            )

        self.assertEqual(api.last_put[0], "/api/rag/sources/source-1")
        self.assertEqual(api.last_put[1]["source_uri"], "replacement.txt")
        self.assertEqual(api.last_put[1]["content"], "replacement file text")


class _View:
    def __init__(self) -> None:
        self.sources_shown = False
        self.error = ""
        self.reset_editor_count = 0

    def show_sources(self, sources):
        self.sources_shown = True

    def show_source_detail(self, source):
        self.source = source

    def show_error(self, message):
        self.error = message

    def show_message(self, message):
        self.message = message

    def reset_editor(self):
        self.reset_editor_count += 1


class _Service:
    def list_sources(self):
        return []

    def create_text_source(self, payload):
        self.created = payload
        return {}

    def replace_with_file(self, source_id, **kwargs):
        self.replaced_file = {"source_id": source_id, **kwargs}
        return {}

    def replace_source(self, source_id, payload):
        self.replaced = {"source_id": source_id, **payload}
        return {}

    def delete_source(self, source_id):
        self.deleted = source_id
        return {}


class _Api:
    def get(self, path):
        return []

    def post(self, path, payload):
        self.last_post = (path, payload)
        return {}

    def put(self, path, payload):
        self.last_put = (path, payload)
        return {}

    def delete(self, path):
        self.last_delete = path


if __name__ == "__main__":
    unittest.main()
