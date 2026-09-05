# Backend

Minimal FastAPI foundation for the Student Attendance System.

## Stack

Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, and Pydantic.

## Setup

From the `backend/` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set `DATABASE_URL` when database features are added. A placeholder is available in the repository root as `.env.example`.

## Run

```bash
uvicorn app.main:app --reload
```

The health endpoint is available at `GET http://127.0.0.1:8000/health`.