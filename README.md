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

### Run PostgreSQL and Redis with Docker Compose

Start the supporting databases locally with Docker Compose:

```bash
docker compose up -d postgres redis
```

The services expose the default ports (`5432` for PostgreSQL, `6379` for Redis) on your host machine. After they start, add the following entries to your `.env` file (create one at the project root if you have not already) so the application can connect to the containers:

```env
DATABASE_URL=postgresql+asyncpg://planner:planner@localhost:5432/planner
REDIS_URL=redis://localhost:6379/0

# Optional: override these if you change the Docker Compose values
POSTGRES_DB=planner
POSTGRES_USER=planner
POSTGRES_PASSWORD=planner
```

Feel free to adjust the credentials in both `docker-compose.yml` and your `.env` file if you prefer different usernames, passwords, or database names.

## Project structure

- `app/` – FastAPI application code, including domain schemas, services, and API routes
- `docs/` – design documents and research

## Additional resources

- [Personal AI Planner Design Document](docs/personal_ai_planner_design.md)
