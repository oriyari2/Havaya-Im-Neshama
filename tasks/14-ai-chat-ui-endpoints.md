# Task 14: AI Consultation API and Desktop UI

## Objective
Build the FastAPI endpoints and PySide6 MVP components to enable user interaction with the AI agent, utilizing the `LLMClient` established in Task 13.

## Requirements
1. **Backend API:**
   - Create a new route (e.g., `POST /api/ai/consult`) that accepts a user prompt.
   - Inject and use the `LLMClient` to generate a response from the local Ollama server.
2. **Desktop UI (PySide6):**
   - Implement the MVP pattern: create `ai_chat_view.py` and `ai_chat_presenter.py`.
   - The view should include a scrollable read-only text area for chat history, an input field for new messages, and a submit button (with loading state indication).
   - Ensure proper right-to-left (RTL) text alignment for Hebrew text in the chat interface, applying the text-direction automation principles established in RTL-Fixer.
3. **Desktop Integration:**
   - Add a navigation element (e.g., a button or menu item) in the main shell to access the AI consultation view.
   - Wire the presenter to communicate with the new FastAPI endpoint via the existing API client.

## Constraints
- Maintain the strict separation of concerns dictated by the MVP and CQRS architecture.
- Do not implement RAG data retrieval logic yet; the LLM should currently answer based purely on its base knowledge.