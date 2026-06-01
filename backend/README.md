# Face Attendance MVP Backend

FastAPI backend for the web-based attendance MVP.

## Run

```powershell
cd "C:\Users\X1 Yoga\hust\pttkht"
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8080
```

Open:

```text
http://127.0.0.1:8080/docs
```

## Main endpoints

- `GET /api/health`
- `GET|POST /api/classes`
- `GET|POST /api/students`
- `GET|POST /api/courses`
- `GET|POST /api/class-courses`
- `GET|POST /api/cameras`
- `POST /api/students/{student_id}/face-profile`
- `POST /api/students/{student_id}/face-profile/images`
- `GET|POST /api/attendance-sessions`
- `POST /api/attendance-sessions/{session_id}/open`
- `POST /api/attendance-sessions/{session_id}/close`
- `POST /api/attendance-sessions/{session_id}/lock`
- `POST /api/attendance-sessions/{session_id}/reopen`
- `POST /api/attendance-sessions/{session_id}/cancel`
- `POST /api/attendance-sessions/{session_id}/manual-attendance`
- `GET /api/attendance-sessions/{session_id}/roster`
- `GET /api/attendance-sessions/{session_id}/audits`
- `POST /api/recognition/image`
- `POST /api/recognition/confirm`
- `GET|POST /api/attendance-logs`
- `PATCH /api/attendance-logs/{log_id}`
- `GET /api/attendance-logs/{log_id}/audits`

## Attendance lifecycle

- `DRAFT`: buoi moi tao, chua cho quet/ghi diem danh.
- `OPEN`: cho phep recognition va confirm attendance.
- `CLOSED`: da dong buoi; khi close tu `OPEN`, backend tu tao `ABSENT` cho sinh vien chua co log.
- `LOCKED`: da khoa, khong cho sua attendance log.
- `CANCELLED`: da huy, khong cho ghi diem danh.

## Attendance log rules

- `POST /api/recognition/image` chi tao `RecognitionEvent`, khong tao `AttendanceLog`.
- `POST /api/recognition/confirm` moi tao log chinh thuc voi `method = FACE`.
- Diem danh thu cong tao/cap nhat log voi `method = MANUAL`.
- Close session tu dong tao log vang voi `method = AUTO_ABSENT`.
- Roster dung `method = NONE` cho sinh vien chua co log, khong luu `NONE` vao DB.
- Moi sinh vien chi co mot attendance log trong mot session.
- Sua log chi duoc khi session `OPEN` hoac `CLOSED`; moi thay doi status/note/method se tao audit.

## Environment

```powershell
$env:DATABASE_URL="sqlite:///backend_attendance.db"
$env:BACKEND_DATABASE_URL="sqlite:///backend_attendance.db"
$env:COMPREFACE_BASE_URL="http://localhost:8000"
$env:COMPREFACE_RECOGNITION_API_KEY="your-recognition-api-key"
$env:ATTENDANCE_RECOGNITION_THRESHOLD="0.97"
```

The default database is `backend_attendance.db`, separate from the older desktop app's `attendance.db`.
