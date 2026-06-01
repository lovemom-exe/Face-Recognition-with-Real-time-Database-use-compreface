"""
db_config.py - Cấu hình kết nối Database
Hệ thống Điểm danh Tự động - Bách Khoa

Hướng dẫn cấu hình:
    - PostgreSQL: postgresql://user:password@localhost:5432/attendance_db
    - MySQL:      mysql+pymysql://user:password@localhost:3306/attendance_db
    - SQLite (Test): sqlite:///attendance.db
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import Base

# ============================================================
# CẤU HÌNH KẾT NỐI
# Ưu tiên đọc từ biến môi trường, fallback sang SQLite để dev/test
# ============================================================
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///attendance.db"  # Mặc định SQLite cho dev (thay bằng PostgreSQL/MySQL khi deploy)
)

# Tạo Engine
engine = create_engine(
    DATABASE_URL,
    echo=False,           # True = in SQL debug ra console
    pool_pre_ping=True,   # Kiểm tra kết nối trước mỗi query (chống mất kết nối)
    pool_size=5,          # Số kết nối tối đa trong pool
    max_overflow=10,      # Số kết nối overflow cho phép
)

# Tạo Session Factory
SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Scoped Session (thread-safe, phù hợp ứng dụng multi-thread như client_app.py)
ScopedSession = scoped_session(SessionFactory)


def init_db():
    """Khởi tạo database: Tạo tất cả bảng nếu chưa tồn tại"""
    Base.metadata.create_all(bind=engine)
    print("[DB] ✅ Database đã được khởi tạo thành công!")


def get_session():
    """Lấy một phiên làm việc (session) mới"""
    return ScopedSession()


def close_session():
    """Đóng scoped session (gọi khi kết thúc thread)"""
    ScopedSession.remove()
