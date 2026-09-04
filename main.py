from fastapi import FastAPI
from fastapi.responses import FileResponse

from excel_report import create_attendance_report


app = FastAPI(
    title="Attendance Excel Report API",
    description="API for exporting attendance reports to Excel",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Attendance Excel Report API is running"
    }


@app.get("/attendance/report/excel")
def export_attendance_report():
    data = [
        {
            "student_id": 1,
            "student_code": "SV001",
            "student_name": "Nguyen Van A",
            "total_sessions": 10,
            "present": 8,
            "absent": 2,
            "late": 1,
            "attendance_rate": 80,
            "absence_rate": 20
        },
        {
            "student_id": 2,
            "student_code": "SV002",
            "student_name": "Tran Thi B",
            "total_sessions": 10,
            "present": 9,
            "absent": 1,
            "late": 0,
            "attendance_rate": 90,
            "absence_rate": 10
        }
    ]

    filename = "attendance_report.xlsx"

    create_attendance_report(
        data,
        filename
    )

    return FileResponse(
        path=filename,
        filename=filename,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )