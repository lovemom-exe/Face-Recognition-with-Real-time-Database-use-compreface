# Activity diagrams

## 1. Mục đích

Activity diagram mô tả quy trình nghiệp vụ, các bước xử lý, điều kiện rẽ nhánh và kết quả đầu ra.

## 2. Quy trình đăng ký và duyệt giảng viên

```mermaid
flowchart TD
    A([Bắt đầu]) --> B[Giảng viên mở form đăng ký]
    B --> C[Nhập họ tên, email trường, mật khẩu]
    C --> D{Email thuộc domain trường?}
    D -- Không --> E[Thông báo email không hợp lệ]
    E --> Z([Kết thúc])
    D -- Có --> F{Email đã tồn tại?}
    F -- Có --> G[Thông báo email đã đăng ký]
    G --> Z
    F -- Không --> H[Tạo user TEACHER trạng thái PENDING]
    H --> I[Thông báo chờ admin duyệt]
    I --> J[Admin xem danh sách PENDING]
    J --> K{Admin duyệt?}
    K -- Không --> L[Giữ trạng thái PENDING hoặc khóa]
    K -- Có --> M[Chuyển user sang ACTIVE]
    M --> N[Giảng viên đăng nhập được]
    L --> Z
    N --> Z
```

## 3. Quy trình điểm danh bằng camera

```mermaid
flowchart TD
    A([Bắt đầu]) --> B[Giảng viên chọn session OPEN]
    B --> C[Chọn camera đầu vào]
    C --> D[Bật camera]
    D --> E[Bắt đầu quét frame]
    E --> F[Gửi frame lên backend]
    F --> G[Backend gọi CompreFace recognize]
    G --> H{Có kết quả nhận diện?}
    H -- Không --> I[Hiển thị UNKNOWN]
    H -- Có --> J{Similarity đủ ngưỡng?}
    J -- Không --> K[Hiển thị LOW_CONFIDENCE]
    J -- Có --> L{Subject đã map FaceProfile?}
    L -- Không --> M[Hiển thị UNMAPPED_SUBJECT]
    L -- Có --> N[Tìm Student từ FaceProfile]
    N --> O{Sinh viên thuộc lớp của session?}
    O -- Không --> P[Hiển thị MATCHED_OUT_OF_CLASS]
    O -- Có --> Q[Hiển thị MATCHED_IN_CLASS]
    Q --> R{Giảng viên xác nhận đúng?}
    R -- Không --> S[Bỏ qua hoặc đánh dấu không đúng]
    R -- Có --> T{Đã có attendance log?}
    T -- Có --> U[Thông báo đã điểm danh]
    T -- Không --> V[Tạo AttendanceLog method FACE]
    I --> W([Kết thúc lượt quét])
    K --> W
    M --> W
    P --> W
    S --> W
    U --> W
    V --> W
```

## 4. Quy trình đóng buổi điểm danh

```mermaid
flowchart TD
    A([Bắt đầu]) --> B[Giảng viên bấm đóng session]
    B --> C[Lấy AttendanceSession]
    C --> D{Session status?}
    D -- OPEN --> E[Lấy danh sách sinh viên trong lớp]
    E --> F[Lấy log đã có trong session]
    F --> G[Tìm sinh viên chưa có log]
    G --> H[Tạo ABSENT với method AUTO_ABSENT]
    H --> I[Chuyển session sang CLOSED]
    I --> J[Trả summary điểm danh]
    D -- CLOSED --> K[Không tạo log trùng]
    K --> J
    D -- LOCKED --> L[Trả lỗi session đã khóa]
    D -- CANCELLED --> M[Trả lỗi session đã hủy]
    J --> Z([Kết thúc])
    L --> Z
    M --> Z
```

## 5. Bảng trạng thái nhận diện

| Trạng thái | Ý nghĩa | Hành động frontend |
|---|---|---|
| `MATCHED_IN_CLASS` | Nhận diện ra sinh viên thuộc lớp của session | Cho phép giảng viên xác nhận điểm danh |
| `MATCHED_OUT_OF_CLASS` | Nhận diện ra sinh viên nhưng không thuộc lớp | Cảnh báo, không tự tạo log chính thức |
| `UNMAPPED_SUBJECT` | Subject CompreFace chưa map với sinh viên | Cảnh báo cần map hồ sơ khuôn mặt |
| `LOW_CONFIDENCE` | Similarity thấp | Cần kiểm tra lại |
| `UNKNOWN` | Không nhận diện được khuôn mặt hợp lệ | Không tạo log |

## 6. Mapping với code hiện tại

| Activity | Code liên quan |
|---|---|
| Đăng ký/duyệt giảng viên | `AuthService`, `UserService`, `auth.py`, `users.py` |
| Điểm danh camera | `recognition.py`, `CompreFaceClient`, `FaceProfile`, `RecognitionEvent` |
| Xác nhận điểm danh | `recognition/confirm`, `AttendanceLog` |
| Đóng session | `attendance_sessions.py`, `AttendanceSession`, `AttendanceLog` |

