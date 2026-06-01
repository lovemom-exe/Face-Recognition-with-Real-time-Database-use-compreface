from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ClassCourse, Course
from ..serializers import class_course_to_dict, course_to_dict

router = APIRouter(prefix="/api", tags=["courses"])


class CourseIn(BaseModel):
    course_code: str
    course_name: str
    credits: int = 0
    status: str = "ACTIVE"


class CourseUpdate(BaseModel):
    course_code: str | None = None
    course_name: str | None = None
    credits: int | None = None
    status: str | None = None


class ClassCourseIn(BaseModel):
    class_id: int
    course_id: int
    teacher_id: int | None = None
    semester: str = ""
    status: str = "ACTIVE"


@router.get("/courses")
def list_courses(include_disabled: bool = False, db: Session = Depends(get_db)):
    query = db.query(Course)
    if not include_disabled:
        query = query.filter(Course.status == "ACTIVE")
    return [course_to_dict(item) for item in query.order_by(Course.course_code).all()]


@router.post("/courses")
def create_course(payload: CourseIn, db: Session = Depends(get_db)):
    item = Course(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return course_to_dict(item)


@router.get("/courses/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    item = db.get(Course, course_id)
    if not item:
        raise HTTPException(status_code=404, detail="Course not found")
    return course_to_dict(item)


@router.put("/courses/{course_id}")
def update_course(course_id: int, payload: CourseUpdate, db: Session = Depends(get_db)):
    item = db.get(Course, course_id)
    if not item:
        raise HTTPException(status_code=404, detail="Course not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return course_to_dict(item)


@router.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    item = db.get(Course, course_id)
    if not item:
        raise HTTPException(status_code=404, detail="Course not found")
    item.status = "DISABLED"
    db.commit()
    return {"deleted": True}


@router.get("/class-courses")
def list_class_courses(db: Session = Depends(get_db)):
    return [class_course_to_dict(item) for item in db.query(ClassCourse).order_by(ClassCourse.id.desc()).all()]


@router.post("/class-courses")
def create_class_course(payload: ClassCourseIn, db: Session = Depends(get_db)):
    item = ClassCourse(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return class_course_to_dict(item)
