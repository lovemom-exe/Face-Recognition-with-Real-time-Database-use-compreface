from __future__ import annotations

from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..attendance_services import BusinessRuleError
from ..database import get_db
from ..report_services import ReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _raise_business_error(exc: BusinessRuleError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


def _excel_response(filename: str, content: bytes) -> Response:
    encoded = quote(filename)
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )


@router.get("/session/{session_id}")
def session_report(session_id: int, db: Session = Depends(get_db)):
    try:
        return ReportService(db).session_report(session_id)
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.get("/student/{student_id}")
def student_report(
    student_id: int,
    course_id: int | None = None,
    class_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
):
    try:
        return ReportService(db).student_report(
            student_id,
            course_id=course_id,
            class_id=class_id,
            from_date=from_date,
            to_date=to_date,
        )
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.get("/class-course/{class_course_id}")
def class_course_report(
    class_course_id: int,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
):
    try:
        return ReportService(db).class_course_report(class_course_id, from_date=from_date, to_date=to_date)
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.get("/session/{session_id}/export-excel")
def export_session_excel(session_id: int, db: Session = Depends(get_db)):
    try:
        filename, content = ReportService(db).export_session_excel(session_id)
        return _excel_response(filename, content)
    except BusinessRuleError as exc:
        _raise_business_error(exc)


@router.get("/class-course/{class_course_id}/export-excel")
def export_class_course_excel(
    class_course_id: int,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
):
    try:
        filename, content = ReportService(db).export_class_course_excel(class_course_id, from_date=from_date, to_date=to_date)
        return _excel_response(filename, content)
    except BusinessRuleError as exc:
        _raise_business_error(exc)
