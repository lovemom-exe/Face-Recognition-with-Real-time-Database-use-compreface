"""
crud.py - Các hàm CRUD (Create, Read, Update, Delete) & Ghi log Điểm danh
Hệ thống Điểm danh Tự động - Bách Khoa

Sử dụng:
    from database.crud import StudentCRUD, AttendanceCRUD

    # Thêm sinh viên
    student = StudentCRUD.create("Nguyễn Văn A", "CNTT-K20", "nguyen_van_a")

    # Ghi log điểm danh
    log = AttendanceCRUD.log_attendance("nguyen_van_a", similarity=0.985)
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import and_
from database.models import Student, AttendanceLog, AttendanceSession
from database.db_config import get_session


# ============================================================
# STUDENT CRUD - Thêm / Sửa / Xóa / Tìm Sinh viên
# ============================================================

class StudentCRUD:
    """Các thao tác CRUD cho bảng students"""

    @staticmethod
    def create(full_name: str, class_name: str, compreface_name: str) -> Student:
        """
        Thêm mới một sinh viên.

        Args:
            full_name: Họ và Tên đầy đủ (VD: "Nguyễn Văn A")
            class_name: Lớp (VD: "CNTT-K20")
            compreface_name: Tên đã đăng ký trên CompreFace

        Returns:
            Student object đã được lưu vào DB

        Raises:
            IntegrityError: Nếu compreface_name đã tồn tại
        """
        session = get_session()
        try:
            student = Student(
                full_name=full_name,
                class_name=class_name,
                compreface_name=compreface_name
            )
            session.add(student)
            session.commit()
            session.refresh(student)
            print(f"[CRUD] ✅ Đã thêm sinh viên: {student}")
            return student
        except Exception as e:
            session.rollback()
            print(f"[CRUD] ❌ Lỗi thêm sinh viên: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def get_by_id(student_id: int) -> Optional[Student]:
        """Tìm sinh viên theo ID"""
        session = get_session()
        try:
            return session.query(Student).filter(Student.id == student_id).first()
        finally:
            session.close()

    @staticmethod
    def get_by_compreface_name(compreface_name: str) -> Optional[Student]:
        """
        Tìm sinh viên theo tên CompreFace.
        Đây là hàm quan trọng nhất - được gọi khi AI nhận diện trả về tên.
        """
        session = get_session()
        try:
            return session.query(Student).filter(
                Student.compreface_name == compreface_name
            ).first()
        finally:
            session.close()

    @staticmethod
    def get_all() -> List[Student]:
        """Lấy danh sách tất cả sinh viên"""
        session = get_session()
        try:
            return session.query(Student).order_by(Student.id).all()
        finally:
            session.close()

    @staticmethod
    def get_by_class(class_name: str) -> List[Student]:
        """Lấy danh sách sinh viên theo lớp"""
        session = get_session()
        try:
            return session.query(Student).filter(
                Student.class_name == class_name
            ).order_by(Student.full_name).all()
        finally:
            session.close()

    @staticmethod
    def update(student_id: int, **kwargs) -> Optional[Student]:
        """
        Cập nhật thông tin sinh viên.

        Args:
            student_id: ID sinh viên cần sửa
            **kwargs: Các trường cần cập nhật (full_name, class_name, compreface_name)

        Returns:
            Student object đã cập nhật, hoặc None nếu không tìm thấy

        Ví dụ:
            StudentCRUD.update(1, full_name="Trần Văn B", class_name="DTVT-K21")
        """
        session = get_session()
        try:
            student = session.query(Student).filter(Student.id == student_id).first()
            if not student:
                print(f"[CRUD] ⚠️ Không tìm thấy sinh viên ID={student_id}")
                return None

            allowed_fields = {"full_name", "class_name", "compreface_name"}
            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(student, key, value)

            student.updated_at = datetime.now()
            session.commit()
            session.refresh(student)
            print(f"[CRUD] ✅ Đã cập nhật sinh viên: {student}")
            return student
        except Exception as e:
            session.rollback()
            print(f"[CRUD] ❌ Lỗi cập nhật sinh viên: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def delete(student_id: int) -> bool:
        """
        Xóa sinh viên (CASCADE: xóa luôn log điểm danh liên quan).

        Returns:
            True nếu xóa thành công, False nếu không tìm thấy
        """
        session = get_session()
        try:
            student = session.query(Student).filter(Student.id == student_id).first()
            if not student:
                print(f"[CRUD] ⚠️ Không tìm thấy sinh viên ID={student_id}")
                return False

            session.delete(student)
            session.commit()
            print(f"[CRUD] ✅ Đã xóa sinh viên ID={student_id}")
            return True
        except Exception as e:
            session.rollback()
            print(f"[CRUD] ❌ Lỗi xóa sinh viên: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def search(keyword: str) -> List[Student]:
        """Tìm kiếm sinh viên theo tên hoặc lớp (LIKE query)"""
        session = get_session()
        try:
            pattern = f"%{keyword}%"
            return session.query(Student).filter(
                (Student.full_name.ilike(pattern)) |
                (Student.class_name.ilike(pattern)) |
                (Student.compreface_name.ilike(pattern))
            ).all()
        finally:
            session.close()


# ============================================================
# ATTENDANCE CRUD - Ghi log & Truy vấn Điểm danh
# ============================================================

class AttendanceCRUD:
    """Các thao tác ghi log và truy vấn điểm danh"""

    @staticmethod
    def log_attendance(
        compreface_name: str,
        similarity: float = 0.0,
        session_id: Optional[int] = None,
        late_threshold_minutes: int = 15,
        session_start_time: Optional[datetime] = None,
        note: str = ""
    ) -> Optional[AttendanceLog]:
        """
        Ghi log điểm danh - HÀM CHÍNH được gọi từ client_app.py

        Logic tự động:
            1. Tra cứu sinh viên theo compreface_name
            2. Kiểm tra trùng lặp (chống ghi log liên tục trong 5 phút)
            3. Tính trạng thái ON_TIME / LATE dựa trên session hoặc threshold
            4. Lưu log vào database

        Args:
            compreface_name: Tên trả về từ CompreFace API
            similarity: Độ chính xác nhận diện (0.0 - 1.0)
            session_id: ID buổi học (nếu có)
            late_threshold_minutes: Số phút trễ tối đa (mặc định 15)
            session_start_time: Giờ bắt đầu buổi học (tính trạng thái late)
            note: Ghi chú

        Returns:
            AttendanceLog object hoặc None nếu bị chặn bởi dedup
        """
        db_session = get_session()
        try:
            # Bước 1: Tìm sinh viên
            student = db_session.query(Student).filter(
                Student.compreface_name == compreface_name
            ).first()

            if not student:
                print(f"[ATTENDANCE] ⚠️ Không tìm thấy sinh viên với compreface_name='{compreface_name}'")
                return None

            # Bước 2: Chống trùng lặp (Deduplication)
            # Không ghi log nếu sinh viên đã điểm danh trong 5 phút gần nhất
            dedup_window = datetime.now() - timedelta(minutes=5)
            recent_log = db_session.query(AttendanceLog).filter(
                and_(
                    AttendanceLog.student_id == student.id,
                    AttendanceLog.check_in_time >= dedup_window
                )
            ).first()

            if recent_log:
                print(
                    f"[ATTENDANCE] ⏭️ Bỏ qua - {student.full_name} đã điểm danh "
                    f"lúc {recent_log.check_in_time.strftime('%H:%M:%S')}"
                )
                return None

            # Bước 3: Tính trạng thái ON_TIME / LATE
            now = datetime.now()
            status = "ON_TIME"

            if session_id:
                # Nếu có session: dùng start_time + late_threshold của session
                att_session = db_session.query(AttendanceSession).get(session_id)
                if att_session:
                    deadline = att_session.start_time + timedelta(minutes=att_session.late_threshold)
                    if now > deadline:
                        status = "LATE"
            elif session_start_time:
                # Nếu truyền trực tiếp giờ bắt đầu
                deadline = session_start_time + timedelta(minutes=late_threshold_minutes)
                if now > deadline:
                    status = "LATE"

            # Bước 4: Tạo log
            log = AttendanceLog(
                student_id=student.id,
                check_in_time=now,
                status=status,
                similarity=similarity,
                note=note,
                session_id=session_id
            )
            db_session.add(log)
            db_session.commit()
            db_session.refresh(log)

            status_text = "🟢 Hợp lệ" if status == "ON_TIME" else "🟡 Đến muộn"
            print(
                f"[ATTENDANCE] ✅ Điểm danh thành công: {student.full_name} - "
                f"{status_text} - Similarity: {similarity:.2%}"
            )
            return log

        except Exception as e:
            db_session.rollback()
            print(f"[ATTENDANCE] ❌ Lỗi ghi log điểm danh: {e}")
            raise
        finally:
            db_session.close()

    @staticmethod
    def get_logs_by_student(student_id: int, limit: int = 50) -> List[AttendanceLog]:
        """Lấy lịch sử điểm danh của 1 sinh viên"""
        session = get_session()
        try:
            return session.query(AttendanceLog).filter(
                AttendanceLog.student_id == student_id
            ).order_by(AttendanceLog.check_in_time.desc()).limit(limit).all()
        finally:
            session.close()

    @staticmethod
    def get_logs_by_date(
        date: Optional[datetime] = None,
        class_name: Optional[str] = None
    ) -> List[AttendanceLog]:
        """
        Lấy log điểm danh theo ngày (mặc định hôm nay).

        Args:
            date: Ngày cần tra cứu (mặc định = hôm nay)
            class_name: Lọc theo lớp (tùy chọn)
        """
        session = get_session()
        try:
            if date is None:
                date = datetime.now()

            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            query = session.query(AttendanceLog).join(Student).filter(
                and_(
                    AttendanceLog.check_in_time >= start_of_day,
                    AttendanceLog.check_in_time < end_of_day
                )
            )

            if class_name:
                query = query.filter(Student.class_name == class_name)

            return query.order_by(AttendanceLog.check_in_time).all()
        finally:
            session.close()

    @staticmethod
    def get_logs_by_session(session_id: int) -> List[AttendanceLog]:
        """Lấy log điểm danh theo buổi học"""
        session = get_session()
        try:
            return session.query(AttendanceLog).filter(
                AttendanceLog.session_id == session_id
            ).order_by(AttendanceLog.check_in_time).all()
        finally:
            session.close()

    @staticmethod
    def get_statistics(
        class_name: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> dict:
        """
        Thống kê điểm danh.

        Returns:
            {
                "total_logs": int,
                "on_time_count": int,
                "late_count": int,
                "on_time_percentage": float,
                "late_percentage": float,
            }
        """
        session = get_session()
        try:
            query = session.query(AttendanceLog).join(Student)

            if class_name:
                query = query.filter(Student.class_name == class_name)
            if from_date:
                query = query.filter(AttendanceLog.check_in_time >= from_date)
            if to_date:
                query = query.filter(AttendanceLog.check_in_time <= to_date)

            all_logs = query.all()
            total = len(all_logs)

            if total == 0:
                return {
                    "total_logs": 0,
                    "on_time_count": 0,
                    "late_count": 0,
                    "on_time_percentage": 0.0,
                    "late_percentage": 0.0,
                }

            on_time = sum(1 for log in all_logs if log.status == "ON_TIME")
            late = total - on_time

            return {
                "total_logs": total,
                "on_time_count": on_time,
                "late_count": late,
                "on_time_percentage": round(on_time / total * 100, 2),
                "late_percentage": round(late / total * 100, 2),
            }
        finally:
            session.close()

    @staticmethod
    def delete_log(log_id: int) -> bool:
        """Xóa một log điểm danh"""
        session = get_session()
        try:
            log = session.query(AttendanceLog).filter(AttendanceLog.id == log_id).first()
            if not log:
                return False
            session.delete(log)
            session.commit()
            print(f"[ATTENDANCE] ✅ Đã xóa log ID={log_id}")
            return True
        except Exception as e:
            session.rollback()
            print(f"[ATTENDANCE] ❌ Lỗi xóa log: {e}")
            raise
        finally:
            session.close()


# ============================================================
# SESSION CRUD - Quản lý buổi học (Tùy chọn)
# ============================================================

class SessionCRUD:
    """Các thao tác CRUD cho bảng attendance_sessions"""

    @staticmethod
    def create(
        session_name: str,
        class_name: str,
        start_time: datetime,
        late_threshold: int = 15
    ) -> AttendanceSession:
        """Tạo buổi học mới"""
        session = get_session()
        try:
            att_session = AttendanceSession(
                session_name=session_name,
                class_name=class_name,
                start_time=start_time,
                late_threshold=late_threshold
            )
            session.add(att_session)
            session.commit()
            session.refresh(att_session)
            print(f"[SESSION] ✅ Đã tạo buổi học: {att_session}")
            return att_session
        except Exception as e:
            session.rollback()
            print(f"[SESSION] ❌ Lỗi tạo buổi học: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def get_active_session(class_name: str) -> Optional[AttendanceSession]:
        """
        Lấy buổi học đang diễn ra (trong ngày hôm nay) cho một lớp.
        Hữu ích để tự động gán session_id khi điểm danh.
        """
        session = get_session()
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)

            return session.query(AttendanceSession).filter(
                and_(
                    AttendanceSession.class_name == class_name,
                    AttendanceSession.start_time >= today_start,
                    AttendanceSession.start_time < today_end
                )
            ).order_by(AttendanceSession.start_time.desc()).first()
        finally:
            session.close()
