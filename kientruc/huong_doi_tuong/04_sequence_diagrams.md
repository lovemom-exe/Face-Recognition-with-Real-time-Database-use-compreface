# Sequence diagrams

## 1. Mục đích

Sequence diagram mô tả thứ tự gửi thông điệp giữa các actor, UI, API, service, repository, database và CompreFace trong một luồng nghiệp vụ cụ thể.

## 2. Giảng viên đăng ký và admin duyệt

```mermaid
sequenceDiagram
    actor Teacher as Giảng viên
    actor Admin as Admin
    participant UI as Frontend
    participant AuthAPI as Auth API
    participant AuthService as AuthService
    participant UserRepo as UserRepository
    participant DB as Database
    participant UserAPI as User API
    participant UserService as UserService

    Teacher->>UI: Nhập họ tên, email trường, mật khẩu
    UI->>AuthAPI: POST /api/v1/auth/register-teacher
    AuthAPI->>AuthService: register_teacher(payload)
    AuthService->>AuthService: Validate domain email
    AuthService->>UserRepo: Kiểm tra email trùng
    AuthService->>DB: Tạo User role TEACHER, status PENDING
    AuthService-->>UI: Tài khoản chờ admin duyệt

    Admin->>UI: Mở màn Tài khoản
    UI->>UserAPI: GET /api/v1/users?role=TEACHER&status=PENDING
    UserAPI->>UserService: list_users()
    UserService->>DB: Lấy danh sách giảng viên PENDING
    DB-->>UI: Danh sách chờ duyệt
    Admin->>UI: Bấm Duyệt
    UI->>UserAPI: POST /api/v1/users/{id}/approve
    UserAPI->>UserService: approve_teacher(id)
    UserService->>DB: status ACTIVE, is_active true
    UserService-->>UI: Duyệt thành công
```

## 3. Admin tạo lớp tín chỉ và phân công giảng viên

```mermaid
sequenceDiagram
    actor Admin as Admin
    participant UI as Frontend
    participant CourseAPI as ClassCourse API
    participant AssignAPI as TeacherAssignment API
    participant Permission as PermissionService
    participant DB as Database

    Admin->>UI: Chọn lớp, môn, kỳ học và giảng viên chính
    UI->>CourseAPI: POST /api/class-courses
    CourseAPI->>DB: Tạo ClassCourse(class_id, course_id, teacher_id, semester)
    CourseAPI-->>UI: Lớp tín chỉ đã tạo
    opt Có giảng viên phụ hoặc phân công bổ sung
        Admin->>UI: Chọn giảng viên và lớp tín chỉ
        UI->>AssignAPI: POST /api/v1/teacher-assignments
        AssignAPI->>DB: Tạo TeacherAssignment
        AssignAPI-->>UI: Phân công thành công
    end
    UI->>Permission: Sau khi giảng viên đăng nhập, tính phạm vi lớp được truy cập
    Permission->>DB: Đọc ClassCourse.teacher_id và TeacherAssignment
    Permission-->>UI: Chỉ trả dữ liệu trong phạm vi được phân công
```

## 4. Map sinh viên với subject CompreFace

```mermaid
sequenceDiagram
    actor Admin as Admin
    participant UI as Frontend
    participant FaceAPI as Face Profile API
    participant StudentRepo as Student Repository
    participant FaceProfile as FaceProfile
    participant CompreFace as CompreFaceClient
    participant DB as Database

    Admin->>UI: Chọn sinh viên và subject CompreFace
    UI->>FaceAPI: POST /api/students/{student_id}/face-profile
    FaceAPI->>StudentRepo: Kiểm tra sinh viên tồn tại
    FaceAPI->>CompreFace: Kiểm tra subject tồn tại
    CompreFace-->>FaceAPI: Subject hợp lệ
    FaceAPI->>DB: Kiểm tra subject chưa map sinh viên khác
    FaceAPI->>FaceProfile: Tạo/cập nhật profile ACTIVE
    FaceProfile->>DB: Lưu student_id, compreface_subject
    FaceAPI-->>UI: Hồ sơ khuôn mặt đã map
```

## 5. Camera nhận diện sinh viên trong session đang mở

```mermaid
sequenceDiagram
    actor Teacher as Giảng viên
    participant UI as Trạm camera
    participant RecognitionAPI as Recognition API
    participant RecognitionService as RecognitionService
    participant AI as CompreFaceClient
    participant DB as Database
    participant Permission as PermissionService

    Teacher->>UI: Chọn session OPEN, bật camera, bắt đầu quét
    UI->>RecognitionAPI: POST /api/recognition/image + frame
    RecognitionAPI->>Permission: ensure_session(current_user, session_id)
    Permission-->>RecognitionAPI: Có quyền truy cập session
    RecognitionAPI->>RecognitionService: recognize_image(frame, session)
    RecognitionService->>AI: recognize(frame)
    AI-->>RecognitionService: subject, similarity, box
    RecognitionService->>DB: Tạo RecognitionEvent
    RecognitionService->>DB: Tìm FaceProfile theo subject
    alt Subject chưa map
        RecognitionService-->>UI: UNMAPPED_SUBJECT
    else Similarity thấp
        RecognitionService-->>UI: LOW_CONFIDENCE
    else Có sinh viên
        RecognitionService->>DB: Kiểm tra sinh viên thuộc lớp của session
        RecognitionService-->>UI: MATCHED_IN_CLASS hoặc MATCHED_OUT_OF_CLASS
    end
```

## 6. Giảng viên xác nhận điểm danh

```mermaid
sequenceDiagram
    actor Teacher as Giảng viên
    participant UI as Frontend
    participant RecognitionAPI as Recognition API
    participant LogService as AttendanceLogService
    participant Permission as PermissionService
    participant DB as Database

    Teacher->>UI: Bấm "Đúng sinh viên này"
    UI->>RecognitionAPI: POST /api/recognition/confirm
    RecognitionAPI->>Permission: ensure_session(user, session_id)
    Permission-->>RecognitionAPI: Có quyền
    RecognitionAPI->>LogService: confirm_attendance(event_id, student_id, session_id)
    LogService->>DB: Kiểm tra session đang OPEN
    LogService->>DB: Kiểm tra sinh viên thuộc lớp
    LogService->>DB: Kiểm tra log trùng student_id + session_id
    alt Đã có log
        LogService-->>UI: ALREADY_ATTENDED
    else Hợp lệ
        LogService->>DB: Tạo AttendanceLog method FACE
        LogService-->>UI: CONFIRMED
    end
```

## 7. Đóng session và tự tạo log vắng

```mermaid
sequenceDiagram
    actor Teacher as Giảng viên
    participant UI as Frontend
    participant SessionAPI as Attendance Session API
    participant SessionService as AttendanceSessionService
    participant DB as Database

    Teacher->>UI: Bấm đóng buổi điểm danh
    UI->>SessionAPI: POST /api/attendance-sessions/{id}/close
    SessionAPI->>SessionService: close(session_id)
    SessionService->>DB: Lấy session
    alt Session OPEN
        SessionService->>DB: Lấy danh sách sinh viên trong lớp
        SessionService->>DB: Lấy attendance logs hiện có
        SessionService->>DB: Tạo ABSENT/AUTO_ABSENT cho sinh viên chưa có log
        SessionService->>DB: Chuyển session CLOSED
        SessionService-->>UI: Summary số có mặt/vắng
    else Session CLOSED
        SessionService-->>UI: Trả summary hiện tại, không tạo trùng
    else LOCKED hoặc CANCELLED
        SessionService-->>UI: Trả lỗi nghiệp vụ
    end
```

## 8. Mapping với DFD

| DFD hiện có | Sequence diagram tương ứng |
|---|---|
| P2 Quản lý khuôn mặt | Map sinh viên với subject CompreFace |
| P3 Nhận diện realtime | Camera nhận diện sinh viên |
| P4 Xử lý điểm danh | Xác nhận điểm danh |
| P5 Tra cứu báo cáo | Có thể bổ sung sequence export báo cáo ở giai đoạn sau |
