# Class diagram

## 1. Mục đích

Class diagram mô tả các lớp chính của hệ thống, thuộc tính quan trọng, phương thức nghiệp vụ tiêu biểu và quan hệ giữa các lớp. Khác với ERD, class diagram không chỉ mô tả bảng dữ liệu mà còn mô tả service, repository và integration.

## 2. Class diagram

```mermaid
classDiagram
    class User {
        +int id
        +string username
        +string email
        +string full_name
        +string role
        +string status
        +bool is_active
    }

    class Student {
        +int id
        +string student_code
        +string full_name
        +string cohort
        +string major
        +string status
    }

    class StudyClass {
        +int id
        +string class_code
        +string class_name
        +string school_year
        +string status
    }

    class Course {
        +int id
        +string course_code
        +string course_name
        +int credits
        +string status
    }

    class ClassCourse {
        +int id
        +int class_id
        +int course_id
        +int teacher_id
        +string semester
        +string status
    }

    class FaceProfile {
        +int id
        +int student_id
        +string compreface_subject
        +int sample_count
        +string status
    }

    class AttendanceSession {
        +int id
        +int class_course_id
        +string session_name
        +datetime start_time
        +datetime end_time
        +string status
    }

    class Camera {
        +int id
        +string camera_code
        +string name
        +string location
        +string status
    }

    class RecognitionEvent {
        +int id
        +int session_id
        +int camera_id
        +string subject
        +float similarity
        +string result_type
        +datetime detected_at
    }

    class AttendanceLog {
        +int id
        +int session_id
        +int student_id
        +string status
        +string method
        +float similarity
        +datetime check_in_time
    }

    class AttendanceLogAudit {
        +int id
        +int attendance_log_id
        +string old_status
        +string new_status
        +string reason
        +datetime changed_at
    }

    class AuthService {
        +register_teacher()
        +login()
        +change_password()
    }

    class PermissionService {
        +accessible_class_ids()
        +ensure_class_course()
        +ensure_session()
    }

    class RecognitionService {
        +recognize_image()
        +map_subject_to_student()
        +classify_result()
    }

    class AttendanceSessionService {
        +open()
        +close()
        +lock()
        +reopen()
        +cancel()
    }

    class AttendanceLogService {
        +confirm_attendance()
        +manual_attendance()
        +update_log()
        +create_audit()
    }

    class ReportService {
        +attendance_summary()
        +class_report()
        +export_excel()
    }

    class CompreFaceClient {
        +list_subjects()
        +create_subject()
        +upload_image()
        +recognize()
    }

    class UserRepository {
        +get_by_login()
        +get_by_email()
        +list()
    }

    class TeacherAssignmentRepository {
        +list()
        +get()
    }

    StudyClass "1" --> "0..*" Student : has
    StudyClass "1" --> "0..*" ClassCourse : opens
    Course "1" --> "0..*" ClassCourse : belongs to
    User "1" --> "0..*" ClassCourse : teaches
    ClassCourse "1" --> "0..*" AttendanceSession : schedules
    Student "1" --> "0..1" FaceProfile : owns
    Student "1" --> "0..*" AttendanceLog : has
    AttendanceSession "1" --> "0..*" RecognitionEvent : records
    AttendanceSession "1" --> "0..*" AttendanceLog : contains
    Camera "1" --> "0..*" RecognitionEvent : captures
    Camera "1" --> "0..*" AttendanceLog : records
    FaceProfile "1" --> "0..*" RecognitionEvent : matched by
    RecognitionEvent "0..1" --> "0..1" AttendanceLog : confirms
    AttendanceLog "1" --> "0..*" AttendanceLogAudit : audited by

    AuthService ..> UserRepository
    PermissionService ..> User
    PermissionService ..> ClassCourse
    RecognitionService ..> CompreFaceClient
    RecognitionService ..> FaceProfile
    RecognitionService ..> RecognitionEvent
    AttendanceSessionService ..> AttendanceSession
    AttendanceLogService ..> AttendanceLog
    AttendanceLogService ..> AttendanceLogAudit
    ReportService ..> AttendanceLog
```

## 3. Nhóm class

| Nhóm | Class | Trách nhiệm |
|---|---|---|
| Domain/entity | `User`, `Student`, `StudyClass`, `Course`, `ClassCourse` | Lưu thông tin người dùng, sinh viên, lớp, môn và lớp tín chỉ |
| Face recognition | `FaceProfile`, `RecognitionEvent`, `CompreFaceClient` | Quản lý subject CompreFace và sự kiện nhận diện |
| Attendance | `AttendanceSession`, `AttendanceLog`, `AttendanceLogAudit`, `Camera` | Quản lý buổi điểm danh, log chính thức, audit và camera |
| Service | `AuthService`, `PermissionService`, `AttendanceSessionService`, `AttendanceLogService`, `RecognitionService`, `ReportService` | Điều phối nghiệp vụ |
| Repository | `UserRepository`, `TeacherAssignmentRepository`, repository đề xuất | Đóng gói truy cập dữ liệu |

## 4. Mapping với code hiện tại

| Class trong thiết kế | Code hiện tại |
|---|---|
| Entity/domain class | `backend/app/models.py` |
| Auth/permission/user service | `backend/app/services/` |
| API controller/router | `backend/app/api/v1/`, `backend/app/routers/` |
| CompreFace integration | `backend/app/compreface_client.py` |
| Serializer/response mapping | `backend/app/serializers.py` |

## 5. Ghi chú thiết kế

Một số service như `RecognitionService`, `AttendanceSessionService`, `AttendanceLogService` có thể đang được triển khai một phần trong router hoặc service cũ. Trong báo cáo OOAD, vẫn nên mô hình hóa chúng thành service riêng để làm rõ trách nhiệm nghiệp vụ và hướng refactor lâu dài.

