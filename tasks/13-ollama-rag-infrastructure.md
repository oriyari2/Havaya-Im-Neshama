# Task 13: RAG Infrastructure & Ollama Client connection

## Objective
The Ollama server is already running locally on port 11434. Your task is strictly to set up the backend infrastructure to communicate with it.

## Requirements
1. **Environment Setup:**
   - Update `backend/app/core/environment.py` (and `.env.example`) to include an `OLLAMA_URL` variable (defaulting to `http://localhost:11434`).
2. **RAG Client:**
   - Inside the `rag/` directory, create a client file (e.g., `llm_client.py`) that uses `httpx` or `requests` to send a prompt to the local Ollama API (`/api/generate` or `/api/chat`) and returns the response.
   - Create a base class or interface for the LLM interaction to allow seamless injection of context for future RAG queries.
3. **Integration:**
   - Ensure the client can be easily imported and used by the FastAPI services when building the AI agent consultation feature.

## Constraints
- Do NOT create any Docker configurations or shell scripts. Assume the LLM service is fully operational at `http://localhost:11434`.
- Adhere to the project's existing modular architecture.