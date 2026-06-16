# Phân tích thiết kế hướng đối tượng

Folder này bổ sung bộ tài liệu OOAD/UML cho hệ thống điểm danh bằng nhận diện khuôn mặt. Bộ tài liệu này không thay thế các tài liệu FDD, DFD, ERD hiện có; nó dùng để nhìn hệ thống dưới góc độ đối tượng, trách nhiệm, tương tác và vòng đời.

## Mục tiêu

- Xác định actor và use case chính của hệ thống.
- Xác định các lớp miền nghiệp vụ, service, repository và quan hệ giữa chúng.
- Mô tả các luồng tương tác quan trọng bằng sequence diagram.
- Mô tả quy trình xử lý nghiệp vụ bằng activity diagram.
- Mô tả vòng đời trạng thái của các đối tượng quan trọng bằng state diagram.
- Mô tả cách chia package/component khi triển khai backend, frontend và CompreFace.

## Danh sách tài liệu

| File | Nội dung |
|---|---|
| `01_tong_quan_ooad.md` | Tổng quan cách chuyển từ phân tích hướng cấu trúc sang hướng đối tượng |
| `02_use_case_diagram.md` | Actor, use case và use case diagram |
| `03_class_diagram.md` | Class diagram cho entity, service, repository và integration |
| `04_sequence_diagrams.md` | Sequence diagram cho các luồng nghiệp vụ chính |
| `05_activity_diagrams.md` | Activity diagram cho đăng ký/duyệt giảng viên và điểm danh camera |
| `06_state_diagrams.md` | State diagram cho `User`, `AttendanceSession`, `FaceProfile`, `AttendanceLog` |
| `07_package_component_diagram.md` | Package/component diagram cho kiến trúc triển khai |
| `diagrams/*.mmd` | Mermaid diagram tách riêng để render hoặc đưa vào báo cáo |

## Diagram tách riêng

| File | Nội dung |
|---|---|
| `diagrams/use_case.mmd` | Use case tổng thể |
| `diagrams/class_diagram.mmd` | Class diagram tổng thể |
| `diagrams/sequence_teacher_register.mmd` | Sequence đăng ký và duyệt giảng viên |
| `diagrams/sequence_class_course_assignment.mmd` | Sequence tạo lớp tín chỉ và phân công giảng viên |
| `diagrams/sequence_face_profile_mapping.mmd` | Sequence map sinh viên với subject CompreFace |
| `diagrams/sequence_camera_attendance.mmd` | Sequence nhận diện camera |
| `diagrams/sequence_confirm_attendance.mmd` | Sequence xác nhận điểm danh |
| `diagrams/sequence_close_session.mmd` | Sequence đóng session |
| `diagrams/activity_camera_attendance.mmd` | Activity điểm danh camera |
| `diagrams/activity_teacher_approval.mmd` | Activity đăng ký/duyệt giảng viên |
| `diagrams/state_attendance_session.mmd` | State session điểm danh |
| `diagrams/state_user.mmd` | State tài khoản người dùng |
| `diagrams/state_face_profile.mmd` | State hồ sơ khuôn mặt |
| `diagrams/state_attendance_log.mmd` | State attendance log |
| `diagrams/package_component.mmd` | Package/component diagram |

## Mapping với tài liệu hướng cấu trúc

| Tài liệu hướng cấu trúc | Tài liệu OOAD tương ứng | Ý nghĩa chuyển đổi |
|---|---|---|
| FDD | Use case diagram | Từ phân rã chức năng sang mục tiêu/tương tác của actor |
| DFD | Sequence và activity diagram | Từ luồng dữ liệu sang chuỗi thông điệp và quy trình xử lý |
| ERD | Class diagram | Từ bảng dữ liệu sang đối tượng miền nghiệp vụ và quan hệ |
| Kiến trúc hệ thống | Package/component diagram | Từ tầng kỹ thuật sang module/package triển khai |

## Ghi chú

Hệ thống hiện tại vẫn có thể trình bày theo hướng cấu trúc. Bộ OOAD này dùng để bổ sung góc nhìn hướng đối tượng cho báo cáo phân tích thiết kế hệ thống, đặc biệt khi cần giải thích class, service, repository, use case và vòng đời trạng thái.
