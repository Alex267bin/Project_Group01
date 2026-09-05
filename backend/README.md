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

## Attendance validation limitation

The authoritative `AttendanceRecord` model and Alembic schema do not contain
GPS or IP address fields. The QR attendance API therefore does not perform GPS
or IP validation. Adding those checks requires an explicit specification and
database migration; no such fields are invented here.