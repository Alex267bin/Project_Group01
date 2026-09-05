import unittest
from datetime import datetime

from openpyxl import load_workbook

from app.services.excel_report import build_attendance_report


class ExcelReportTests(unittest.TestCase):
    def test_build_attendance_report_contains_summary_and_details(self) -> None:
        report = build_attendance_report(
            {
                "student_code": "student-1",
                "class_id": "class-1",
                "total_sessions": 2,
                "present": 1,
                "late": 0,
                "absent": 1,
                "absence_rate": 50.0,
                "absence_alert": True,
                "details": [
                    {
                        "session_id": "session-1",
                        "course_name": "Computer Science",
                        "start_time": datetime(2026, 9, 5, 8, 0),
                        "end_time": datetime(2026, 9, 5, 10, 0),
                        "status": "Present",
                    }
                ],
            },
            student_name="Test Student",
        )

        workbook = load_workbook(report)
        summary = workbook["Attendance Summary"]
        details = workbook["Session Details"]

        self.assertEqual(
            [cell.value for cell in summary[1]],
            [
                "Student Code",
                "Student Name",
                "Class ID",
                "Total Sessions",
                "Present",
                "Late",
                "Absent",
                "Absence Rate (%)",
                "Absence Alert",
            ],
        )
        self.assertEqual(summary[2][0].value, "student-1")
        self.assertEqual(summary[2][1].value, "Test Student")
        self.assertEqual(summary[2][7].value, 50.0)
        self.assertEqual(summary[2][8].value, "Yes")
        self.assertEqual(details[2][0].value, "session-1")
        self.assertEqual(details[2][1].value, "Computer Science")
        self.assertEqual(details[2][4].value, "Present")
        self.assertEqual(summary.freeze_panes, "A2")
        self.assertEqual(details.freeze_panes, "A2")


if __name__ == "__main__":
    unittest.main()
