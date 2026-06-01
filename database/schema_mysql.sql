-- ============================================================
-- HỆ THỐNG ĐIỂM DANH TỰ ĐỘNG - DATABASE SCHEMA (MySQL)
-- Phiên bản tương thích MySQL 8.x
-- Ngày tạo: 2026-04-07
-- ============================================================

-- ============================================================
-- BẢNG 1: students - Quản lý thông tin sinh viên
-- ============================================================
CREATE TABLE IF NOT EXISTS students (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(150)    NOT NULL,
    class_name      VARCHAR(50)     NOT NULL,
    compreface_name VARCHAR(150)    NOT NULL UNIQUE,
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_students_compreface_name (compreface_name),
    INDEX idx_students_class_name (class_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- BẢNG 2: attendance_logs - Lịch sử điểm danh
-- ============================================================
CREATE TABLE IF NOT EXISTS attendance_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT             NOT NULL,
    check_in_time   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          ENUM('ON_TIME', 'LATE') NOT NULL DEFAULT 'ON_TIME',
    similarity      DECIMAL(5, 4)   DEFAULT 0.0000,
    note            TEXT            DEFAULT NULL,
    session_id      INT             DEFAULT NULL,

    CONSTRAINT fk_attendance_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_attendance_session
        FOREIGN KEY (session_id)
        REFERENCES attendance_sessions(id)
        ON DELETE SET NULL,

    INDEX idx_attendance_student_id (student_id),
    INDEX idx_attendance_check_in_time (check_in_time),
    INDEX idx_attendance_student_time (student_id, check_in_time),
    INDEX idx_attendance_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- BẢNG BỔ SUNG: attendance_sessions - Quản lý buổi học
-- ============================================================
CREATE TABLE IF NOT EXISTS attendance_sessions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    session_name    VARCHAR(200)    NOT NULL,
    class_name      VARCHAR(50)     NOT NULL,
    start_time      TIMESTAMP       NOT NULL,
    late_threshold  INT             NOT NULL DEFAULT 15,
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
