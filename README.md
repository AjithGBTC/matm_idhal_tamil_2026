# Tamil Nadu Matrimony SaaS

Greenfield monorepo for a multi-tenant matrimony administration platform. The current implementation starts with the shared platform shell and tenant/subscription administration; later modules are tracked in `docs/architecture.md`.

## Repository inspection

At initial inspection the workspace contained only a Python virtual environment. There was no existing frontend, backend source, database schema, migrations, package manifest, or repository guidance. FastAPI is available in the environment; SQLAlchemy is not currently installed. No existing functionality or data has been changed.

## Run

Backend (PowerShell, from the workspace root):

```powershell
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
Set-Location backend
..\.venv\Scripts\alembic.exe upgrade head
..\.venv\Scripts\python.exe scripts\bootstrap.py --name "Platform Admin" --email admin@example.com
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Run the frontend commands from the workspace root (use `Set-Location ..` after the backend setup commands).

## Checks

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m pytest tests
Set-Location ..\frontend
npm run build
```

FastAPI serves interactive API documentation at `http://localhost:8000/docs` after startup.

The initial local database is SQLite for easy development. Relative SQLite paths are resolved from the `backend` directory so bootstrap and API use the same file even when launched from different directories. Configure MySQL with `DATABASE_URL` for deployment. Set a private, randomly generated `JWT_SECRET_KEY` in `backend/.env` before the first login and before running outside local development. The bootstrap command asks for the initial password without echoing it and refuses to create a second platform admin.

