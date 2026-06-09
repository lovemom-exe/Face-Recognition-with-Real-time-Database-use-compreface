# Face Attendance MVP Backend

FastAPI backend for the web-based attendance MVP.

## Run

```powershell
cd "C:\Users\X1 Yoga\hust\pttkht"
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8080
```

Open:

```text
http://127.0.0.1:8080/docs
```

Create the first admin account:

```powershell
.\.venv\Scripts\python.exe scripts\create_admin.py --username admin --email admin@example.com --full-name "System Admin"
```

All business APIs are protected after Phase 3. Login first with `POST /api/v1/auth/login`, then send:

```http
Authorization: Bearer <access_token>
```

## Main endpoints

- `GET /api/health`
- `POST /api/v1/auth/register-teacher`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/change-password`
- `GET /api/v1/auth/me`
- `GET|POST|PATCH|DELETE /api/v1/users`
- `POST /api/v1/users/{user_id}/approve`
- `POST /api/v1/users/{user_id}/disable`
- `GET|POST|DELETE /api/v1/teacher-assignments`
- `GET|PATCH /api/v1/settings`
- `GET /api/v1/audit-logs`
- `GET /api/v1/health/db`
- `GET /api/v1/health/compreface`
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
$env:DATABASE_URL="sqlite:///backend_attendance.db"
$env:JWT_SECRET_KEY="change-me-generate-with-secrets-token-urlsafe"
$env:PASSWORD_PEPPER="change-me-random-pepper"
$env:COMPREFACE_BASE_URL="http://localhost:8000"
$env:COMPREFACE_API_KEY="your-recognition-api-key"
$env:ATTENDANCE_RECOGNITION_THRESHOLD="0.75"
$env:ALLOWED_TEACHER_EMAIL_DOMAINS="hust.edu.vn"
```

The default database is `backend_attendance.db`, separate from the older desktop app's `attendance.db`.

For PostgreSQL local development, start `docker-compose.postgres.yml`, set `DATABASE_URL`, then run Alembic:

```powershell
docker compose -f docker-compose.postgres.yml up -d
$env:DATABASE_URL="postgresql+psycopg2://face_attendance:face_attendance_password@127.0.0.1:5432/face_attendance"
.\.venv\Scripts\alembic.exe upgrade head
```

If local port `5432` is already used, run Docker with `POSTGRES_PORT=55432` and use port `55432` in `DATABASE_URL`.

## Phase 3 security notes

- Frontend must call backend through `/api` and include the JWT bearer token.
- Admin/Staff can manage system data.
- Teacher can only access classes, courses, sessions, attendance logs, reports and face profiles in assigned scopes.
- Assign teachers through `/api/v1/teacher-assignments`.
- Request id, request logging, security headers, upload validation, rate limit, audit logs, health checks and backup scripts are available.

## Teacher account flow

- Teacher registers with `POST /api/v1/auth/register-teacher` using a school email domain configured by `ALLOWED_TEACHER_EMAIL_DOMAINS`.
- New teacher accounts are created with role `TEACHER`, status `PENDING`, and cannot log in yet.
- Admin approves a teacher with `POST /api/v1/users/{user_id}/approve`.
- Admin creates class-course rows and can assign the primary teacher through `class_courses.teacher_id`.
- Extra/co-teacher access can be granted through `/api/v1/teacher-assignments`.
- Teachers log in with school email or username, then can change their own password with `/api/v1/auth/change-password`.
