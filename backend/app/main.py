from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.attendance import router as attendance_router
from app.api.leave_requests import router as leave_requests_router
from app.api.sessions import router as sessions_router
from app.api.statistics import router as statistics_router


app = FastAPI(title="Student Attendance System")

app.include_router(auth_router)
app.include_router(attendance_router)
app.include_router(leave_requests_router)
app.include_router(sessions_router)
app.include_router(statistics_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}