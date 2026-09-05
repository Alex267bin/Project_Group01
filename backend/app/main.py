from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.sessions import router as sessions_router


app = FastAPI(title="Student Attendance System")

app.include_router(auth_router)
app.include_router(sessions_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}