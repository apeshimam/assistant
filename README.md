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

## Staying up to date with GitHub

Ensure your local checkout tracks the latest code from GitHub before you start working:

1. Confirm that a remote named `origin` is configured. If this repository was cloned fresh, it should already exist. If it is missing, add it with your GitHub URL:

   ```bash
   git remote add origin https://github.com/<your-username>/assistant.git
   ```

2. Fetch the newest commits and rebase or fast-forward your local branch so it reflects GitHub's current state:

   ```bash
   git fetch origin
   git checkout main  # or the branch you track remotely
   git pull --ff-only origin main
   ```

3. For feature work on another branch (for example, `work`), rebase it onto the freshly updated base branch:

   ```bash
   git checkout work
   git rebase main
   ```

Following this flow before making changes guarantees that the repository starts from the latest GitHub revision.
