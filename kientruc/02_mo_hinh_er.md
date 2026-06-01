# Mo hinh ER

## 1. ERD de xuat

Mo hinh ER ben duoi mo rong tu schema hien tai. Ba bang dang co trong code la `students`, `attendance_sessions`, `attendance_logs`. Cac thuc the `CLASS`, `COURSE`, `FACE_PROFILE`, `RECOGNITION_EVENT`, `CAMERA`, `USER` la phan de xuat de he thong quan ly day du hon.

```mermaid
erDiagram
    USER ||--o{ ATTENDANCE_SESSION : creates
    CLASS ||--o{ STUDENT : has
    CLASS ||--o{ ATTENDANCE_SESSION : schedules
    COURSE ||--o{ ATTENDANCE_SESSION : belongs_to
    STUDENT ||--|| FACE_PROFILE : owns
    STUDENT ||--o{ ATTENDANCE_LOG : has
    ATTENDANCE_SESSION ||--o{ ATTENDANCE_LOG : contains
    CAMERA ||--o{ ATTENDANCE_LOG : records
    FACE_PROFILE ||--o{ RECOGNITION_EVENT : matches
    ATTENDANCE_LOG ||--o| RECOGNITION_EVENT : based_on

    USER {
        int id PK
        string username UK
        string password_hash
        string full_name
        string role
        datetime created_at
    }

    CLASS {
        int id PK
        string class_code UK
        string class_name
        string school_year
    }

    STUDENT {
        int id PK
        string student_code UK
        string full_name
        int class_id FK
        string compreface_name UK
        datetime created_at
        datetime updated_at
    }

    COURSE {
        int id PK
        string course_code UK
        string course_name
        int credit
    }

    ATTENDANCE_SESSION {
        int id PK
        int class_id FK
        int course_id FK
        int created_by FK
        string session_name
        datetime start_time
        int late_threshold
        string status
        datetime created_at
    }

    FACE_PROFILE {
        int id PK
        int student_id FK
        string compreface_name UK
        int sample_count
        string status
        datetime last_enrolled_at
    }

    CAMERA {
        int id PK
        string camera_code UK
        string location
        string stream_url
        string status
    }

    RECOGNITION_EVENT {
        int id PK
        int face_profile_id FK
        int camera_id FK
        datetime detected_at
        decimal similarity
        string result_type
        string image_ref
    }

    ATTENDANCE_LOG {
        int id PK
        int student_id FK
        int session_id FK
        int camera_id FK
        int recognition_event_id FK
        datetime check_in_time
        string status
        decimal similarity
        string note
    }
```

## 2. Tu dien thuc the

| Thuc the | Y nghia | Mapping hien tai |
|---|---|---|
| `USER` | Tai khoan giao vien/quan tri vien | Chua co |
| `CLASS` | Lop hoc/hoc phan theo nien khoa | Dang luu don gian bang `students.class_name` |
| `STUDENT` | Thong tin sinh vien | `students` |
| `COURSE` | Mon hoc | Chua co |
| `ATTENDANCE_SESSION` | Buoi hoc/buoi diem danh | `attendance_sessions` |
| `FACE_PROFILE` | Ho so khuon mat cua sinh vien tren CompreFace | Chua co bang rieng; dang nam trong `students.compreface_name` |
| `CAMERA` | Thiet bi/cua diem danh | Chua co |
| `RECOGNITION_EVENT` | Su kien nhan dien raw, ke ca unknown/rejected | Chua co |
| `ATTENDANCE_LOG` | Ban ghi diem danh hop le | `attendance_logs` |

## 3. Quan he va ban so

| Quan he | Ban so | Giai thich |
|---|---|---|
| `CLASS` - `STUDENT` | 1 - N | Mot lop co nhieu sinh vien; mot sinh vien thuoc mot lop chinh |
| `CLASS` - `ATTENDANCE_SESSION` | 1 - N | Mot lop co nhieu buoi hoc can diem danh |
| `COURSE` - `ATTENDANCE_SESSION` | 1 - N | Mot mon hoc co nhieu buoi hoc |
| `STUDENT` - `FACE_PROFILE` | 1 - 1 | Moi sinh vien co mot ho so khuon mat dang active |
| `STUDENT` - `ATTENDANCE_LOG` | 1 - N | Mot sinh vien co nhieu lan diem danh |
| `ATTENDANCE_SESSION` - `ATTENDANCE_LOG` | 1 - N | Mot buoi hoc co nhieu log diem danh |
| `FACE_PROFILE` - `RECOGNITION_EVENT` | 1 - N | Mot ho so khuon mat co the phat sinh nhieu su kien nhan dien |
| `RECOGNITION_EVENT` - `ATTENDANCE_LOG` | 0/1 - 0/1 | Mot su kien hop le co the tao mot log diem danh |
| `CAMERA` - `ATTENDANCE_LOG` | 1 - N | Mot camera ghi nhan nhieu log |

## 4. Rang buoc du lieu

| Ma | Rang buoc |
|---|---|
| C01 | `student_code` va `compreface_name` phai duy nhat |
| C02 | `similarity` nam trong khoang 0.0000 den 1.0000 |
| C03 | `attendance_log` khong duoc tao neu khong tim thay sinh vien |
| C04 | Trong cung mot `session_id`, moi sinh vien chi co mot log hop le dau tien |
| C05 | `check_in_time` phai nam trong khoang cho phep cua buoi hoc neu he thong bat rang buoc thoi gian |
| C06 | `FACE_PROFILE.status = ACTIVE` moi duoc dung cho nhan dien diem danh |
| C07 | Khi xoa sinh vien, log diem danh nen duoc giu voi ma sinh vien snapshot neu can bao cao lich su; code hien tai dang cascade delete |

## 5. Thiet ke toi thieu neu giu schema hien tai

Neu muon it thay doi code, co the giu 3 bang chinh:

| Bang | Khoa chinh | Thuoc tinh quan trong |
|---|---|---|
| `students` | `id` | `full_name`, `class_name`, `compreface_name` |
| `attendance_sessions` | `id` | `session_name`, `class_name`, `start_time`, `late_threshold` |
| `attendance_logs` | `id` | `student_id`, `session_id`, `check_in_time`, `status`, `similarity` |

Khi viet bao cao, nen trinh bay ERD de xuat day du, sau do ghi chu phien ban code hien tai dang la ban toi thieu cua ERD nay.
