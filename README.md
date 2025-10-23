# assistant

This repository contains the code and design documentation for the Personal AI Planner project.

## Getting started

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

2. Launch the FastAPI application with Uvicorn:

   ```bash
   uvicorn app.main:app --reload
   ```

3. Open http://localhost:8000/daily for the keyboard-friendly planner UI or http://localhost:8000/docs to explore the interactive API documentation.

## Project structure

- `app/` – FastAPI application code, including domain schemas, services, and API routes
- `docs/` – design documents and research

## Additional resources

- [Personal AI Planner Design Document](docs/personal_ai_planner_design.md)
