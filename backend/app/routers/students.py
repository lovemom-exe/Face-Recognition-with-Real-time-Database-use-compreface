from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AttendanceLog, AttendanceSession, Student, StudyClass
from ..serializers import attendance_log_to_dict, student_to_dict

router = APIRouter(prefix="/api/students", tags=["students"])


class StudentIn(BaseModel):
    student_code: str
    full_name: str
    class_id: int | None = None
    email: str | None = None
    cohort: str | None = None
    major: str | None = None
    status: str = "ACTIVE"


class StudentUpdate(BaseModel):
    student_code: str | None = None
    full_name: str | None = None
    class_id: int | None = None
    email: str | None = None
    cohort: str | None = None
    major: str | None = None
    status: str | None = None


@router.get("")
def list_students(
    class_id: int | None = None,
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Student)
    if class_id is not None:
        query = query.filter(Student.class_id == class_id)
    if q:
        pattern = f"%{q}%"
        query = query.filter(or_(Student.full_name.ilike(pattern), Student.student_code.ilike(pattern)))
    return [student_to_dict(item) for item in query.order_by(Student.full_name).all()]


@router.post("")
def create_student(payload: StudentIn, db: Session = Depends(get_db)):
    item = Student(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return student_to_dict(item)


@router.post("/import-csv")
async def import_students_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    created = 0
    updated = 0
    skipped = 0
    errors: list[dict[str, str]] = []
    seen_codes: set[str] = set()

    for index, row in enumerate(reader, start=2):
        student_code = (row.get("student_code") or row.get("ma_sv") or row.get("code") or "").strip()
        full_name = (row.get("full_name") or row.get("ho_ten") or row.get("name") or "").strip()
        email = (row.get("email") or "").strip() or None
        cohort = (row.get("cohort") or row.get("khoa_hoc") or row.get("khoa") or "").strip() or None
        major = (row.get("major") or row.get("nganh") or "").strip() or None
        class_id_raw = (row.get("class_id") or "").strip()
        class_code = (row.get("class_code") or row.get("ma_lop") or "").strip()
        class_name = (row.get("class_name") or row.get("ten_lop") or class_code).strip()
        school_year = (row.get("school_year") or row.get("nam_hoc") or "").strip() or None

        if not student_code or not full_name:
            skipped += 1
            errors.append({"line": str(index), "error": "Thiếu mã sinh viên hoặc họ tên."})
            continue
        if student_code in seen_codes:
            skipped += 1
            errors.append({"line": str(index), "student_code": student_code, "error": "Mã sinh viên bị trùng trong file CSV."})
            continue
        seen_codes.add(student_code)

        class_id = int(class_id_raw) if class_id_raw.isdigit() else None
        if class_id:
            exists = db.get(StudyClass, class_id)
            if not exists:
                skipped += 1
                errors.append({"line": str(index), "student_code": student_code, "error": "class_id không tồn tại."})
                continue
        elif class_code:
            study_class = db.query(StudyClass).filter(StudyClass.class_code == class_code).first()
            if not study_class:
                study_class = StudyClass(
                    class_code=class_code,
                    class_name=class_name or class_code,
                    school_year=school_year,
                )
                db.add(study_class)
                db.flush()
            class_id = study_class.id if study_class else None
        else:
            skipped += 1
            errors.append({"line": str(index), "student_code": student_code, "error": "Thiếu class_id hoặc mã lớp."})
            continue

        student = db.query(Student).filter(Student.student_code == student_code).first()
        if student:
            student.full_name = full_name
            student.email = email
            student.cohort = cohort
            student.major = major
            student.class_id = class_id
            student.status = "ACTIVE"
            updated += 1
        else:
            db.add(Student(student_code=student_code, full_name=full_name, email=email, class_id=class_id, cohort=cohort, major=major))
            created += 1

    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors[:20]}


@router.get("/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    item = db.get(Student, student_id)
    if not item:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_to_dict(item)


@router.get("/{student_id}/attendance-summary")
def get_student_attendance_summary(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    total_sessions = 0
    if student.class_id:
        total_sessions = db.query(AttendanceSession).join(AttendanceSession.class_course).filter(
            AttendanceSession.status.in_(["OPEN", "CLOSED"]),
            AttendanceSession.class_course.has(class_id=student.class_id),
        ).count()

    logs_query = db.query(AttendanceLog).join(AttendanceLog.session).filter(AttendanceLog.student_id == student.id)
    if student.class_id:
        logs_query = logs_query.filter(
            AttendanceSession.status.in_(["OPEN", "CLOSED"]),
            AttendanceSession.class_course.has(class_id=student.class_id),
        )
    logs = logs_query.order_by(AttendanceLog.check_in_time.desc()).all()
    attended = len({log.session_id for log in logs})
    absent = max(total_sessions - attended, 0)
    late = sum(1 for log in logs if log.status == "LATE")

    return {
        "student": student_to_dict(student),
        "total_sessions": total_sessions,
        "attended_sessions": attended,
        "absent_sessions": absent,
        "late_sessions": late,
        "logs": [attendance_log_to_dict(log) for log in logs[:20]],
    }


@router.put("/{student_id}")
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    item = db.get(Student, student_id)
    if not item:
        raise HTTPException(status_code=404, detail="Student not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return student_to_dict(item)


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    item = db.get(Student, student_id)
    if not item:
        raise HTTPException(status_code=404, detail="Student not found")
    item.status = "DISABLED"
    db.commit()
    return {"deleted": True}
