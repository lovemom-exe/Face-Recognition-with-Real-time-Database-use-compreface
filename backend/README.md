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
- `POST /api/recognition/image`
- `GET|POST /api/attendance-logs`

## Environment

```powershell
$env:BACKEND_DATABASE_URL="sqlite:///backend_attendance.db"
$env:COMPREFACE_BASE_URL="http://localhost:8000"
$env:COMPREFACE_RECOGNITION_API_KEY="your-recognition-api-key"
$env:ATTENDANCE_RECOGNITION_THRESHOLD="0.97"
```

The default database is `backend_attendance.db`, separate from the older desktop app's `attendance.db`.
