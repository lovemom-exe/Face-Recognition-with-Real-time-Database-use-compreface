"""
models.py - SQLAlchemy ORM Models
Hệ thống Điểm danh Tự động - Bách Khoa
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Numeric, Enum, ForeignKey,
    create_engine, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Student(Base):
    """Bảng quản lý thông tin sinh viên"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(150), nullable=False, comment="Họ và Tên đầy đủ")
    class_name = Column(String(50), nullable=False, comment="Lớp (VD: CNTT-K20)")
    compreface_name = Column(
        String(150), nullable=False, unique=True,
        comment="Tên đăng ký trên CompreFace (khóa tra cứu từ API nhận diện)"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Quan hệ 1-N: Một sinh viên có nhiều log điểm danh
    attendance_logs = relationship(
        "AttendanceLog", back_populates="student",
        cascade="all, delete-orphan", lazy="dynamic"
    )

    __table_args__ = (
        Index("idx_students_compreface_name", "compreface_name"),
        Index("idx_students_class_name", "class_name"),
    )

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.full_name}', class='{self.class_name}')>"

    def to_dict(self):
        """Chuyển đổi sang dictionary (tiện cho API / JSON)"""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "class_name": self.class_name,
            "compreface_name": self.compreface_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AttendanceSession(Base):
    """Bảng quản lý buổi học (tùy chọn)"""
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_name = Column(String(200), nullable=False, comment="Tên buổi học")
    class_name = Column(String(50), nullable=False, comment="Lớp áp dụng")
    start_time = Column(DateTime, nullable=False, comment="Giờ bắt đầu (mốc tính on_time/late)")
    late_threshold = Column(Integer, nullable=False, default=15, comment="Số phút trễ tối đa")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Quan hệ 1-N
    attendance_logs = relationship("AttendanceLog", back_populates="session", lazy="dynamic")

    def __repr__(self):
        return f"<AttendanceSession(id={self.id}, name='{self.session_name}')>"


class AttendanceLog(Base):
    """Bảng lịch sử điểm danh"""
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    check_in_time = Column(DateTime, nullable=False, default=datetime.now, comment="Thời điểm điểm danh")
    status = Column(
        Enum("ON_TIME", "LATE", name="attendance_status"),
        nullable=False, default="ON_TIME",
        comment="Trạng thái: ON_TIME=Hợp lệ, LATE=Đến muộn"
    )
    similarity = Column(Numeric(5, 4), default=0.0, comment="Độ chính xác nhận diện (0.0 - 1.0)")
    note = Column(Text, default="", comment="Ghi chú tùy chọn")
    session_id = Column(
        Integer, ForeignKey("attendance_sessions.id", ondelete="SET NULL"),
        nullable=True
    )

    # Quan hệ N-1
    student = relationship("Student", back_populates="attendance_logs")
    session = relationship("AttendanceSession", back_populates="attendance_logs")

    __table_args__ = (
        Index("idx_attendance_student_id", "student_id"),
        Index("idx_attendance_check_in_time", "check_in_time"),
        Index("idx_attendance_student_time", "student_id", "check_in_time"),
        Index("idx_attendance_session_id", "session_id"),
    )

    def __repr__(self):
        return (
            f"<AttendanceLog(id={self.id}, student_id={self.student_id}, "
            f"time='{self.check_in_time}', status='{self.status}')>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.full_name if self.student else None,
            "check_in_time": self.check_in_time.isoformat() if self.check_in_time else None,
            "status": self.status,
            "similarity": float(self.similarity) if self.similarity else 0.0,
            "note": self.note,
            "session_id": self.session_id,
        }
