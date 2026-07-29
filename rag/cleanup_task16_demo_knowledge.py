from __future__ import annotations

import sys

from backend.app.application.services.knowledge_management_service import KnowledgeManagementService
from rag.embedding_client import OllamaEmbeddingClient


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    service = KnowledgeManagementService(OllamaEmbeddingClient())
    deleted = service.cleanup_task16_demo_chunks()
    print(f"Deleted {deleted} disposable Task 16 demo knowledge chunk(s).")


if __name__ == "__main__":
    main()
