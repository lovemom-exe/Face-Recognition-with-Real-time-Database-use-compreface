from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import Course, StudyClass, User
from backend.app.utils.password import hash_password


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def admin_user(db_session):
    user = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin",
        role="ADMIN",
        is_active=True,
        status="ACTIVE",
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def teacher_user(db_session):
    user = User(
        username="teacher",
        email="teacher@example.com",
        full_name="Teacher",
        role="TEACHER",
        is_active=True,
        status="ACTIVE",
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def class_course(db_session):
    study_class = StudyClass(class_code="KTPM1", class_name="KTPM 1")
    course = Course(course_code="PPTKHT", course_name="Phan tich thiet ke he thong", credits=3)
    db_session.add_all([study_class, course])
    db_session.commit()
    db_session.refresh(study_class)
    db_session.refresh(course)
    from backend.app.models import ClassCourse

    item = ClassCourse(class_id=study_class.id, course_id=course.id, semester="2026A")
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item
