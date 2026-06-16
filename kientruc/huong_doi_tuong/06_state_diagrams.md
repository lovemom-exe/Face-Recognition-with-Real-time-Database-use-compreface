# State diagrams

## 1. Mục đích

State diagram mô tả vòng đời trạng thái của các đối tượng có thay đổi trạng thái rõ ràng trong quá trình sử dụng hệ thống.

## 2. User

```mermaid
stateDiagram-v2
    [*] --> PENDING: Giảng viên tự đăng ký
    PENDING --> ACTIVE: Admin duyệt
    PENDING --> DISABLED: Admin khóa/từ chối
    ACTIVE --> DISABLED: Admin khóa
    DISABLED --> ACTIVE: Admin mở lại
    ACTIVE --> [*]
```

| Trạng thái | Ý nghĩa |
|---|---|
| `PENDING` | Tài khoản giảng viên mới đăng ký, chưa được đăng nhập |
| `ACTIVE` | Tài khoản hợp lệ, có thể đăng nhập |
| `DISABLED` | Tài khoản bị khóa |

## 3. AttendanceSession

```mermaid
stateDiagram-v2
    [*] --> DRAFT: Tạo session
    DRAFT --> OPEN: Mở điểm danh
    DRAFT --> CANCELLED: Hủy khi chưa có log
    OPEN --> CLOSED: Đóng session
    CLOSED --> OPEN: Reopen nếu được phép
    CLOSED --> LOCKED: Khóa sau khi chốt
    LOCKED --> [*]
    CANCELLED --> [*]
```

| Trạng thái | Ý nghĩa | Quy tắc |
|---|---|---|
| `DRAFT` | Buổi điểm danh mới tạo | Chưa nhận điểm danh |
| `OPEN` | Đang mở điểm danh | Chỉ trạng thái này được confirm attendance |
| `CLOSED` | Đã đóng | Có thể tạo `ABSENT` tự động cho sinh viên chưa có log |
| `LOCKED` | Đã khóa/chốt | Không cho sửa log |
| `CANCELLED` | Đã hủy | Không dùng để điểm danh |

## 4. FaceProfile

```mermaid
stateDiagram-v2
    [*] --> PENDING: Tạo profile hoặc chưa đủ mẫu
    PENDING --> ACTIVE: Map subject và enroll đủ mẫu
    ACTIVE --> RETRAIN_REQUIRED: Chất lượng nhận diện kém
    RETRAIN_REQUIRED --> ACTIVE: Enroll lại thành công
    ACTIVE --> DISABLED: Khóa hồ sơ
    DISABLED --> ACTIVE: Mở lại hồ sơ
```

| Trạng thái | Ý nghĩa |
|---|---|
| `PENDING` | Hồ sơ chưa sẵn sàng nhận diện |
| `ACTIVE` | Subject đã map và có thể dùng để điểm danh |
| `RETRAIN_REQUIRED` | Cần thu thập/enroll lại ảnh |
| `DISABLED` | Hồ sơ bị khóa, không dùng để nhận diện chính thức |

## 5. AttendanceLog

```mermaid
stateDiagram-v2
    [*] --> NOT_RECORDED: Chưa có log trong roster
    NOT_RECORDED --> ON_TIME: Confirm FACE đúng giờ
    NOT_RECORDED --> LATE: Confirm FACE sau ngưỡng muộn
    NOT_RECORDED --> ABSENT: Auto absent khi close session
    NOT_RECORDED --> EXCUSED: Giảng viên/admin sửa có phép
    ON_TIME --> EXCUSED: Sửa thủ công
    LATE --> EXCUSED: Sửa thủ công
    ABSENT --> ON_TIME: Sửa thủ công
    ABSENT --> LATE: Sửa thủ công
    ON_TIME --> INVALID: Đánh dấu không hợp lệ
    LATE --> INVALID: Đánh dấu không hợp lệ
    ABSENT --> INVALID: Đánh dấu không hợp lệ
```

| Trạng thái | Ý nghĩa |
|---|---|
| `NOT_RECORDED` | Chỉ dùng trong roster response, không lưu DB |
| `ON_TIME` | Sinh viên có mặt đúng giờ |
| `LATE` | Sinh viên có mặt muộn |
| `ABSENT` | Sinh viên vắng |
| `EXCUSED` | Vắng có phép hoặc được miễn |
| `PENDING_REVIEW` | Cần giảng viên kiểm tra |
| `INVALID` | Log bị đánh dấu không hợp lệ |

## 6. Ghi chú

Các state diagram này giúp kiểm tra rule nghiệp vụ:

- Không confirm điểm danh nếu session không `OPEN`.
- Không sửa log nếu session `LOCKED` hoặc `CANCELLED`.
- Không cho login nếu user `PENDING` hoặc `DISABLED`.
- Không dùng face profile `DISABLED` cho nhận diện chính thức.

