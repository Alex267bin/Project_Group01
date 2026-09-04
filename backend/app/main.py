from fastapi import FastAPI


app = FastAPI(title="Student Attendance System")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}