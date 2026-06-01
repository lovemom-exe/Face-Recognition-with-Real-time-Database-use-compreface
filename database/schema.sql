-- ============================================================
-- HỆ THỐNG ĐIỂM DANH TỰ ĐỘNG - DATABASE SCHEMA
-- Tương thích: PostgreSQL / MySQL
-- Ngày tạo: 2026-04-07
-- ============================================================

-- ============================================================
-- BẢNG 1: students - Quản lý thông tin sinh viên
-- ============================================================
CREATE TABLE IF NOT EXISTS students (
    id              SERIAL PRIMARY KEY,                    -- ID tự tăng (PostgreSQL)
    full_name       VARCHAR(150)    NOT NULL,               -- Họ và Tên đầy đủ
    class_name      VARCHAR(50)     NOT NULL,               -- Lớp (VD: 'CNTT-K20', 'DTVT-K21')
    compreface_name VARCHAR(150)    NOT NULL UNIQUE,        -- Tên đã đăng ký trên CompreFace (khóa tra cứu)
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(), -- Ngày tạo bản ghi
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW()  -- Ngày cập nhật gần nhất
);

-- Index tăng tốc tra cứu theo tên CompreFace (trả về từ API nhận diện)
CREATE INDEX idx_students_compreface_name ON students(compreface_name);

-- Index tra cứu theo lớp
CREATE INDEX idx_students_class_name ON students(class_name);


-- ============================================================
-- BẢNG 2: attendance_logs - Lịch sử điểm danh
-- ============================================================

-- Enum trạng thái điểm danh
-- PostgreSQL:
CREATE TYPE attendance_status AS ENUM ('ON_TIME', 'LATE');
-- MySQL: Dùng ENUM('ON_TIME', 'LATE') trực tiếp trong cột

CREATE TABLE IF NOT EXISTS attendance_logs (
    id              SERIAL PRIMARY KEY,                     -- ID log tự tăng
    student_id      INTEGER         NOT NULL,               -- FK → students.id
    check_in_time   TIMESTAMP       NOT NULL DEFAULT NOW(), -- Thời điểm điểm danh (timestamp)
    status          attendance_status NOT NULL DEFAULT 'ON_TIME',  -- Trạng thái: Hợp lệ / Đến muộn
    similarity      DECIMAL(5, 4)   DEFAULT 0.0,            -- Độ chính xác nhận diện (0.0000 - 1.0000)
    note            TEXT            DEFAULT '',              -- Ghi chú tùy chọn

    -- Ràng buộc khóa ngoại
    CONSTRAINT fk_attendance_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Index tăng tốc tra cứu log theo sinh viên
CREATE INDEX idx_attendance_student_id ON attendance_logs(student_id);

-- Index tăng tốc tra cứu log theo thời gian (báo cáo, thống kê)
CREATE INDEX idx_attendance_check_in_time ON attendance_logs(check_in_time);

-- Index kết hợp: tìm log của 1 sinh viên trong khoảng thời gian
CREATE INDEX idx_attendance_student_time ON attendance_logs(student_id, check_in_time);


-- ============================================================
-- BẢNG BỔ SUNG (Tùy chọn): attendance_sessions - Quản lý buổi học
-- ============================================================
CREATE TABLE IF NOT EXISTS attendance_sessions (
    id              SERIAL PRIMARY KEY,
    session_name    VARCHAR(200)    NOT NULL,               -- Tên buổi học (VD: "Toán A1 - Buổi 3")
    class_name      VARCHAR(50)     NOT NULL,               -- Lớp áp dụng
    start_time      TIMESTAMP       NOT NULL,               -- Giờ bắt đầu (mốc tính on_time/late)
    late_threshold  INTEGER         NOT NULL DEFAULT 15,    -- Số phút trễ tối đa (mặc định 15 phút)
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Thêm cột session_id vào attendance_logs (liên kết buổi học)
ALTER TABLE attendance_logs
    ADD COLUMN session_id INTEGER REFERENCES attendance_sessions(id) ON DELETE SET NULL;

CREATE INDEX idx_attendance_session_id ON attendance_logs(session_id);
