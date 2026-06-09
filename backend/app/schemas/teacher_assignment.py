from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TeacherAssignmentCreate(BaseModel):
    teacher_id: int
    class_id: int
    course_id: int | None = None
    semester: str = ""


class TeacherAssignmentOut(BaseModel):
    id: int
    teacher_id: int
    class_id: int
    course_id: int | None
    semester: str
    created_at: datetime
    created_by: int | None

    model_config = {"from_attributes": True}
