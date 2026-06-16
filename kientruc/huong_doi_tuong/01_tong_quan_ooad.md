# Tổng quan phân tích thiết kế hướng đối tượng

## 1. Mục đích

Phân tích thiết kế hướng đối tượng tập trung vào các đối tượng trong hệ thống, trách nhiệm của từng đối tượng, quan hệ giữa các đối tượng và cách chúng gửi thông điệp cho nhau để thực hiện nghiệp vụ.

Trong hệ thống điểm danh bằng nhận diện khuôn mặt, hướng đối tượng giúp trả lời các câu hỏi:

- Ai sử dụng hệ thống?
- Hệ thống có những đối tượng nghiệp vụ nào?
- Mỗi đối tượng chịu trách nhiệm gì?
- Các đối tượng tương tác với nhau ra sao khi điểm danh?
- Một buổi điểm danh, hồ sơ khuôn mặt hay tài khoản giảng viên có vòng đời trạng thái như thế nào?

## 2. Vị trí của OOAD trong bộ tài liệu hiện có

Bộ tài liệu cũ trong `kientruc/` đang thiên về hướng cấu trúc:

| Tài liệu hiện có | Góc nhìn chính |
|---|---|
| FDD | Hệ thống có những nhóm chức năng nào |
| DFD | Dữ liệu đi qua tác nhân, tiến trình và kho dữ liệu như thế nào |
| ERD | Dữ liệu được lưu thành bảng và quan hệ ra sao |
| Kiến trúc hệ thống | Hệ thống chia tầng kỹ thuật như thế nào |

Bộ tài liệu OOAD bổ sung góc nhìn:

| Tài liệu OOAD | Góc nhìn chính |
|---|---|
| Use case diagram | Actor muốn đạt mục tiêu gì khi dùng hệ thống |
| Class diagram | Các lớp miền nghiệp vụ, service và repository liên hệ ra sao |
| Sequence diagram | Các đối tượng gửi thông điệp theo thứ tự nào |
| Activity diagram | Quy trình xử lý rẽ nhánh thế nào |
| State diagram | Đối tượng đổi trạng thái qua những sự kiện nào |
| Package/component diagram | Module triển khai phụ thuộc nhau ra sao |

## 3. Các actor chính

| Actor | Vai trò |
|---|---|
| Admin | Tạo dữ liệu nền, duyệt tài khoản giảng viên, phân công lớp tín chỉ |
| Teacher | Tạo/mở buổi điểm danh, bật camera, xác nhận kết quả nhận diện, xem báo cáo |
| Student | Đi qua camera để hệ thống nhận diện và ghi nhận điểm danh |
| Camera/Webcam | Cung cấp frame ảnh đầu vào cho hệ thống |
| CompreFace Service | Nhận ảnh, trả subject và similarity cho backend |

## 4. Các nhóm đối tượng chính

| Nhóm | Đối tượng tiêu biểu |
|---|---|
| Người dùng | `User`, `Teacher`, `Admin` |
| Danh mục đào tạo | `Student`, `StudyClass`, `Course`, `ClassCourse` |
| Khuôn mặt | `FaceProfile`, `RecognitionEvent`, `CompreFaceClient` |
| Điểm danh | `AttendanceSession`, `AttendanceLog`, `AttendanceLogAudit`, `Camera` |
| Dịch vụ nghiệp vụ | `AuthService`, `PermissionService`, `RecognitionService`, `AttendanceSessionService`, `AttendanceLogService`, `ReportService` |
| Truy cập dữ liệu | `UserRepository`, `TeacherAssignmentRepository`, các repository đề xuất cho sinh viên, lớp, buổi điểm danh và log |

## 5. Nguyên tắc thiết kế

| Nguyên tắc | Áp dụng trong hệ thống |
|---|---|
| Encapsulation | Logic nghiệp vụ nằm trong service, không để frontend xử lý trực tiếp |
| Single Responsibility | Mỗi service xử lý một nhóm nghiệp vụ rõ ràng |
| Dependency Direction | Frontend gọi backend; backend gọi database và CompreFace |
| Separation of Concerns | Tách presentation, API, service, repository, database, AI integration |
| Auditability | Các hành động quan trọng như sửa log, duyệt tài khoản, xác nhận điểm danh cần có log/audit |

## 6. Kết luận

Hệ thống có thể được trình bày là:

> Phân tích ban đầu theo hướng cấu trúc bằng FDD, DFD, ERD. Sau đó bổ sung phân tích hướng đối tượng bằng UML để làm rõ actor, use case, class, sequence, activity, state và package/component.

