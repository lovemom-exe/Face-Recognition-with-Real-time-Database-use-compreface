import { useEffect, useMemo, useRef, useState } from 'react'
import {
  AlertTriangle,
  BookOpen,
  Camera,
  CheckCircle2,
  CirclePlus,
  ClipboardList,
  FileImage,
  GraduationCap,
  ImageUp,
  KeyRound,
  LockKeyhole,
  Loader2,
  LogOut,
  Pencil,
  Play,
  RefreshCcw,
  Save,
  Search,
  ShieldCheck,
  Square,
  Trash2,
  UserCheck,
  UserPlus,
  Users,
  Video,
  X,
} from 'lucide-react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const TOKEN_STORAGE_KEY = 'face_attendance_access_token'
const USER_STORAGE_KEY = 'face_attendance_user'

let apiToken = localStorage.getItem(TOKEN_STORAGE_KEY) || ''

function setApiToken(token) {
  apiToken = token || ''
}

const emptyClass = { class_code: '', class_name: '', school_year: '2026' }
const emptyCourse = { course_code: '', course_name: '', credits: 3 }
const emptyStudent = { student_code: '', full_name: '', class_id: '', email: '', cohort: '', major: '' }
const emptyCamera = { camera_code: '', name: '', location: '', stream_url: '' }
const emptyClassCourse = { class_id: '', course_id: '', teacher_id: '', semester: '2026-2' }
const emptySession = { class_course_id: '', session_name: '', start_time: '', late_threshold_minutes: 15 }
const emptyTeacherAssignment = { teacher_id: '', class_course_id: '' }
const emptyPasswordForm = { old_password: '', new_password: '', confirm_password: '' }
const emptyRegisterForm = { email: '', full_name: '', password: '', confirm_password: '' }

async function api(path, options = {}) {
  const baseHeaders = options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }
  if (apiToken) baseHeaders.Authorization = `Bearer ${apiToken}`
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...baseHeaders, ...(options.headers || {}) },
  })
  const text = await response.text()
  const data = text ? JSON.parse(text) : null
  if (!response.ok) {
    const error = new Error(data?.message || data?.detail || `HTTP ${response.status}`)
    error.status = response.status
    error.data = data
    throw error
  }
  return data
}

function toLocalDatetimeValue(date = new Date()) {
  const offset = date.getTimezoneOffset()
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 16)
}

function toApiDatetime(value) {
  return value ? new Date(value).toISOString() : null
}

function Pill({ children, tone = 'neutral' }) {
  return <span className={`pill pill-${tone}`}>{children}</span>
}

const DETECTION_STATUS_LABELS = {
  MATCHED_IN_CLASS: 'Thuộc lớp',
  MATCHED_OUT_OF_CLASS: 'Không thuộc lớp này',
  UNMAPPED_SUBJECT: 'Subject chưa map',
  LOW_CONFIDENCE: 'Cần kiểm tra lại',
  UNKNOWN: 'Không nhận diện được',
  NO_SESSION_SELECTED: 'Chưa chọn buổi',
  AI_SERVICE_ERROR: 'Lỗi CompreFace',
  CONFIRMED: 'Đã điểm danh',
  ALREADY_ATTENDED: 'Đã điểm danh',
}

function detectionTone(status) {
  if (['MATCHED_IN_CLASS', 'CONFIRMED', 'ALREADY_ATTENDED'].includes(status)) return 'ok'
  if (['MATCHED_OUT_OF_CLASS', 'LOW_CONFIDENCE', 'UNMAPPED_SUBJECT'].includes(status)) return 'warn'
  return 'neutral'
}

function formatSimilarity(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'Không có'
  const number = Number(value)
  return number <= 1 ? `${(number * 100).toFixed(1)}%` : `${number.toFixed(2)}%`
}

function detectionKey(item, fallback = '') {
  return item?.event_id || item?.event?.id || fallback
}

function IconButton({ title, children, onClick, type = 'button', disabled }) {
  return (
    <button className="icon-button" type={type} title={title} aria-label={title} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  )
}

function Section({ icon: Icon, title, actions, children }) {
  return (
    <section className="section">
      <div className="section-head">
        <div className="section-title">
          <Icon size={18} />
          <h2>{title}</h2>
        </div>
        {actions ? <div className="section-actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  )
}

function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  )
}

function StatusBar({ status, error }) {
  return (
    <div className="status-bar">
      <div className="status-item">
        <span className={`dot ${status === 'ok' ? 'dot-ok' : status === 'loading' ? 'dot-warn' : 'dot-bad'}`} />
        <span>{status === 'ok' ? 'Backend hoạt động' : status === 'loading' ? 'Đang kiểm tra backend' : 'Backend lỗi'}</span>
      </div>
      {error ? <span className="status-error">{error}</span> : null}
    </div>
  )
}

function LoginScreen({
  mode,
  onModeChange,
  loginForm,
  registerForm,
  onLoginChange,
  onRegisterChange,
  onLoginSubmit,
  onRegisterSubmit,
  error,
  message,
  busy,
}) {
  const isRegister = mode === 'register'
  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={isRegister ? onRegisterSubmit : onLoginSubmit}>
        <div className="login-mark">{isRegister ? <UserPlus size={24} /> : <KeyRound size={24} />}</div>
        <h1>{isRegister ? 'Đăng ký tài khoản giảng viên' : 'Đăng nhập FaceAttend'}</h1>
        <p>
          {isRegister
            ? 'Dùng email trường để tạo tài khoản. Admin sẽ duyệt và phân công lớp tín chỉ trước khi bạn đăng nhập.'
            : 'Giảng viên đăng nhập bằng email trường hoặc tên đăng nhập đã được cấp.'}
        </p>
        {isRegister ? (
          <>
            <Field label="Họ tên giảng viên">
              <input value={registerForm.full_name} onChange={(event) => onRegisterChange('full_name', event.target.value)} autoComplete="name" required />
            </Field>
            <Field label="Email trường">
              <input type="email" value={registerForm.email} onChange={(event) => onRegisterChange('email', event.target.value)} autoComplete="email" required />
            </Field>
            <Field label="Mật khẩu">
              <input type="password" value={registerForm.password} onChange={(event) => onRegisterChange('password', event.target.value)} autoComplete="new-password" required />
            </Field>
            <Field label="Nhập lại mật khẩu">
              <input type="password" value={registerForm.confirm_password} onChange={(event) => onRegisterChange('confirm_password', event.target.value)} autoComplete="new-password" required />
            </Field>
          </>
        ) : (
          <>
            <Field label="Email trường hoặc tên đăng nhập">
              <input value={loginForm.username} onChange={(event) => onLoginChange('username', event.target.value)} autoComplete="username" required />
            </Field>
            <Field label="Mật khẩu">
              <input type="password" value={loginForm.password} onChange={(event) => onLoginChange('password', event.target.value)} autoComplete="current-password" required />
            </Field>
          </>
        )}
        {message ? <div className="login-success">{message}</div> : null}
        {error ? <div className="login-error">{error}</div> : null}
        <button className="primary login-button" type="submit" disabled={busy}>
          {busy ? <Loader2 className="spin" size={17} /> : isRegister ? <UserPlus size={17} /> : <KeyRound size={17} />}
          {isRegister ? 'Đăng ký' : 'Đăng nhập'}
        </button>
        <button className="link-button" type="button" onClick={() => onModeChange(isRegister ? 'login' : 'register')} disabled={busy}>
          {isRegister ? 'Đã có tài khoản? Đăng nhập' : 'Giảng viên chưa có tài khoản? Đăng ký'}
        </button>
      </form>
    </div>
  )
}

function DataTable({ columns, rows, emptyText }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map((col) => <th key={col.key}>{col.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td className="empty" colSpan={columns.length}>{emptyText}</td></tr>
          ) : (
            rows.map((row, index) => (
              <tr key={row.id || index}>
                {columns.map((col) => <td key={col.key}>{col.render ? col.render(row) : row[col.key]}</td>)}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}

function App() {
  const [activeTab, setActiveTab] = useState('directory')
  const [auth, setAuth] = useState(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY) || ''
    const userRaw = localStorage.getItem(USER_STORAGE_KEY)
    setApiToken(token)
    return { token, user: userRaw ? JSON.parse(userRaw) : null }
  })
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [authMode, setAuthMode] = useState('login')
  const [registerForm, setRegisterForm] = useState(emptyRegisterForm)
  const [loginError, setLoginError] = useState('')
  const [registerMessage, setRegisterMessage] = useState('')
  const [passwordForm, setPasswordForm] = useState(emptyPasswordForm)
  const [passwordMessage, setPasswordMessage] = useState('')
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [data, setData] = useState({
    classes: [],
    courses: [],
    students: [],
    cameras: [],
    classCourses: [],
    sessions: [],
    logs: [],
    users: [],
    teacherAssignments: [],
    comprefaceSubjects: [],
    comprefaceStatus: null,
  })
  const [forms, setForms] = useState({
    class: emptyClass,
    course: emptyCourse,
    student: emptyStudent,
    camera: emptyCamera,
    classCourse: emptyClassCourse,
    teacherAssignment: emptyTeacherAssignment,
    session: { ...emptySession, start_time: toLocalDatetimeValue() },
  })
  const [search, setSearch] = useState('')
  const [selectedStudentId, setSelectedStudentId] = useState('')
  const [selectedSubject, setSelectedSubject] = useState('')
  const [faceFiles, setFaceFiles] = useState([])
  const [studentCsvFile, setStudentCsvFile] = useState(null)
  const [editingClassId, setEditingClassId] = useState(null)
  const [editingCourseId, setEditingCourseId] = useState(null)
  const [selectedClassId, setSelectedClassId] = useState('')
  const [classDetail, setClassDetail] = useState(null)
  const [summaryStudentId, setSummaryStudentId] = useState('')
  const [studentSummary, setStudentSummary] = useState(null)

  const [recognitionSessionId, setRecognitionSessionId] = useState('')
  const [recognitionCameraId, setRecognitionCameraId] = useState('')
  const [videoDevices, setVideoDevices] = useState([])
  const [selectedVideoDeviceId, setSelectedVideoDeviceId] = useState('')
  const [isCameraOn, setIsCameraOn] = useState(false)
  const [isScanning, setIsScanning] = useState(false)
  const [isRecognizing, setIsRecognizing] = useState(false)
  const [roster, setRoster] = useState([])
  const [detections, setDetections] = useState([])
  const [rejectedDetectionIds, setRejectedDetectionIds] = useState([])
  const [latestFrameUrl, setLatestFrameUrl] = useState('')

  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const scanTimerRef = useRef(null)

  function clearAuth(message = '') {
    setApiToken('')
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(USER_STORAGE_KEY)
    setAuth({ token: '', user: null })
    setStatus('error')
    setError(message)
    stopCamera()
  }

  function handleApiError(err) {
    if (err?.status === 401) {
      clearAuth('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
      return
    }
    setError(err.message)
  }

  async function handleLogin(event) {
    event.preventDefault()
    setBusy(true)
    setLoginError('')
    setError('')
    try {
      const result = await api('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify(loginForm),
      })
      setApiToken(result.access_token)
      localStorage.setItem(TOKEN_STORAGE_KEY, result.access_token)
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(result.user))
      setAuth({ token: result.access_token, user: result.user })
      setLoginForm({ username: '', password: '' })
      setStatus('loading')
    } catch (err) {
      setLoginError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleRegisterTeacher(event) {
    event.preventDefault()
    setBusy(true)
    setLoginError('')
    setRegisterMessage('')
    setError('')
    if (registerForm.password !== registerForm.confirm_password) {
      setLoginError('Mật khẩu nhập lại chưa khớp.')
      setBusy(false)
      return
    }
    try {
      const result = await api('/api/v1/auth/register-teacher', {
        method: 'POST',
        body: JSON.stringify({
          email: registerForm.email,
          full_name: registerForm.full_name,
          password: registerForm.password,
        }),
      })
      setRegisterForm(emptyRegisterForm)
      setRegisterMessage(result.message || 'Tài khoản đang chờ admin duyệt.')
      setAuthMode('login')
    } catch (err) {
      setLoginError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleLogout() {
    setBusy(true)
    try {
      if (auth.token) await api('/api/v1/auth/logout', { method: 'POST' })
    } catch {
      // Logout locally even if the token is already invalid on the backend.
    } finally {
      setBusy(false)
      clearAuth('Đã đăng xuất.')
    }
  }

  const filteredStudents = useMemo(() => {
    const value = search.trim().toLowerCase()
    if (!value) return data.students
    return data.students.filter((student) => `${student.student_code} ${student.full_name} ${student.class_name || ''}`.toLowerCase().includes(value))
  }, [data.students, search])

  const isAdmin = auth.user?.role === 'ADMIN'
  const canManageCatalog = ['ADMIN', 'STAFF'].includes(auth.user?.role)
  const teacherUsers = data.users.filter((user) => user.role === 'TEACHER')
  const pendingTeachers = teacherUsers.filter((user) => user.status === 'PENDING')
  const openSessions = data.sessions.filter((session) => session.status === 'OPEN')
  const presentCount = roster.filter((student) => student.attendance_status !== 'ABSENT').length

  function teacherName(teacherId) {
    const teacher = teacherUsers.find((item) => Number(item.id) === Number(teacherId))
    return teacher ? `${teacher.full_name} (${teacher.email || teacher.username})` : teacherId ? `ID ${teacherId}` : 'Chưa phân công'
  }

  function classCourseLabel(item) {
    if (!item) return 'Chưa chọn'
    return `${item.class?.class_code || item.class_id} / ${item.course?.course_code || item.course_id} - ${item.semester || 'Chưa có kỳ'}`
  }

  function studyClassName(classId) {
    const studyClass = data.classes.find((item) => Number(item.id) === Number(classId))
    return studyClass ? `${studyClass.class_code} - ${studyClass.class_name}` : `Lớp ID ${classId}`
  }

  function courseName(courseId) {
    const course = data.courses.find((item) => Number(item.id) === Number(courseId))
    return course ? `${course.course_code} - ${course.course_name}` : courseId ? `Môn ID ${courseId}` : 'Tất cả môn'
  }

  async function loadAll() {
    setBusy(true)
    setError('')
    try {
      const [health, classes, courses, students, cameras, classCourses, sessions, logs, comprefaceSubjects, comprefaceStatus] = await Promise.all([
        api('/api/health'),
        api('/api/classes'),
        api('/api/courses'),
        api('/api/students'),
        api('/api/cameras'),
        api('/api/class-courses'),
        api('/api/attendance-sessions'),
        api('/api/attendance-logs'),
        api('/api/compreface/subjects'),
        api('/api/compreface/status'),
      ])
      const [users, teacherAssignments] = isAdmin
        ? await Promise.all([
          api('/api/v1/users?role=TEACHER'),
          api('/api/v1/teacher-assignments'),
        ])
        : [[], []]
      setStatus(health?.status === 'ok' ? 'ok' : 'error')
      setData({
        classes,
        courses,
        students,
        cameras,
        classCourses,
        sessions,
        logs,
        users,
        teacherAssignments,
        comprefaceSubjects: comprefaceSubjects.subjects || [],
        comprefaceStatus,
      })
      if (selectedClassId) {
        const detail = await api(`/api/classes/${selectedClassId}`)
        setClassDetail(detail)
      }
    } catch (err) {
      setStatus('error')
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function loadClassDetail(classId = selectedClassId) {
    if (!classId) {
      setSelectedClassId('')
      setClassDetail(null)
      return
    }
    setBusy(true)
    setError('')
    try {
      const result = await api(`/api/classes/${classId}`)
      setSelectedClassId(String(classId))
      setClassDetail(result)
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function loadRoster(sessionId = recognitionSessionId) {
    if (!sessionId) {
      setRoster([])
      return
    }
    try {
      const result = await api(`/api/attendance-sessions/${sessionId}/roster`)
      setRoster(result.students || [])
    } catch (err) {
      handleApiError(err)
    }
  }

  async function loadVideoDevices() {
    if (!navigator.mediaDevices?.enumerateDevices) return
    const devices = await navigator.mediaDevices.enumerateDevices()
    setVideoDevices(devices.filter((device) => device.kind === 'videoinput'))
  }

  useEffect(() => {
    if (!auth.token) {
      return undefined
    }
    const timer = window.setTimeout(() => {
      loadAll()
      loadVideoDevices()
    }, 0)
    return () => {
      window.clearTimeout(timer)
      stopCamera()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth.token])

  useEffect(() => {
    const timer = window.setTimeout(() => loadRoster(recognitionSessionId), 0)
    return () => window.clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recognitionSessionId])

  function updateForm(name, key, value) {
    setForms((current) => ({ ...current, [name]: { ...current[name], [key]: value } }))
  }

  async function submitJson(path, body, resetName, resetValue) {
    setBusy(true)
    setError('')
    try {
      await api(path, { method: 'POST', body: JSON.stringify(body) })
      if (resetName) setForms((current) => ({ ...current, [resetName]: resetValue }))
      await loadAll()
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function saveClass(event) {
    event.preventDefault()
    const path = editingClassId ? `/api/classes/${editingClassId}` : '/api/classes'
    const method = editingClassId ? 'PUT' : 'POST'
    setBusy(true)
    setError('')
    try {
      await api(path, { method, body: JSON.stringify(forms.class) })
      setForms((current) => ({ ...current, class: emptyClass }))
      setEditingClassId(null)
      await loadAll()
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function saveCourse(event) {
    event.preventDefault()
    const path = editingCourseId ? `/api/courses/${editingCourseId}` : '/api/courses'
    const method = editingCourseId ? 'PUT' : 'POST'
    setBusy(true)
    setError('')
    try {
      await api(path, { method, body: JSON.stringify({ ...forms.course, credits: Number(forms.course.credits) }) })
      setForms((current) => ({ ...current, course: emptyCourse }))
      setEditingCourseId(null)
      await loadAll()
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function deleteItem(path) {
    setBusy(true)
    setError('')
    try {
      await api(path, { method: 'DELETE' })
      await loadAll()
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  function editClass(row) {
    setEditingClassId(row.id)
    setForms((current) => ({ ...current, class: { class_code: row.class_code, class_name: row.class_name, school_year: row.school_year || '' } }))
  }

  function editCourse(row) {
    setEditingCourseId(row.id)
    setForms((current) => ({ ...current, course: { course_code: row.course_code, course_name: row.course_name, credits: row.credits } }))
  }

  async function openSession(sessionId) {
    setBusy(true)
    setError('')
    try {
      await api(`/api/attendance-sessions/${sessionId}/open`, { method: 'POST' })
      await loadAll()
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function closeSession(sessionId) {
    setBusy(true)
    setError('')
    try {
      await api(`/api/attendance-sessions/${sessionId}/close`, { method: 'POST' })
      await loadAll()
      if (String(sessionId) === recognitionSessionId) setRecognitionSessionId('')
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function changePassword(event) {
    event.preventDefault()
    setBusy(true)
    setPasswordMessage('')
    setError('')
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setError('Mật khẩu mới nhập lại chưa khớp.')
      setBusy(false)
      return
    }
    try {
      const result = await api('/api/v1/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({
          old_password: passwordForm.old_password,
          new_password: passwordForm.new_password,
        }),
      })
      setPasswordForm(emptyPasswordForm)
      setPasswordMessage(result.message || 'Đã đổi mật khẩu.')
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function approveTeacher(userId) {
    setBusy(true)
    setError('')
    try {
      await api(`/api/v1/users/${userId}/approve`, { method: 'POST' })
      await loadAll()
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function disableTeacher(userId) {
    setBusy(true)
    setError('')
    try {
      await api(`/api/v1/users/${userId}/disable`, { method: 'POST' })
      await loadAll()
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function createTeacherAssignment(event) {
    event.preventDefault()
    const classCourse = data.classCourses.find((item) => Number(item.id) === Number(forms.teacherAssignment.class_course_id))
    if (!classCourse) {
      setError('Chưa chọn lớp tín chỉ hợp lệ.')
      return
    }
    await submitJson('/api/v1/teacher-assignments', {
      teacher_id: Number(forms.teacherAssignment.teacher_id),
      class_id: Number(classCourse.class_id),
      course_id: Number(classCourse.course_id),
      semester: classCourse.semester || '',
    }, 'teacherAssignment', emptyTeacherAssignment)
  }

  async function createFaceProfile() {
    if (!selectedStudentId) return
    setBusy(true)
    setError('')
    try {
      await api(`/api/students/${selectedStudentId}/face-profile`, {
        method: 'POST',
        body: JSON.stringify({
          compreface_subject: selectedSubject || null,
          status: selectedSubject ? 'ACTIVE' : 'PENDING',
          sample_count: 0,
        }),
      })
      await loadAll()
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function uploadFaceImages() {
    if (!selectedStudentId || faceFiles.length === 0) return
    setBusy(true)
    setError('')
    try {
      const form = new FormData()
      faceFiles.forEach((file) => form.append('files', file))
      await api(`/api/students/${selectedStudentId}/face-profile/images`, { method: 'POST', body: form })
      setFaceFiles([])
      await loadAll()
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function importStudentsCsv() {
    if (!studentCsvFile) return
    setBusy(true)
    setError('')
    try {
      const form = new FormData()
      form.append('file', studentCsvFile)
      const result = await api('/api/students/import-csv', { method: 'POST', body: form })
      setStudentCsvFile(null)
      setError(`CSV: tạo mới ${result.created}, cập nhật ${result.updated}, lỗi/bỏ qua ${result.skipped}`)
      await loadAll()
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function startCamera() {
    setError('')
    try {
      stopCamera()
      const constraints = { video: selectedVideoDeviceId ? { deviceId: { exact: selectedVideoDeviceId } } : true, audio: false }
      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream
      setIsCameraOn(true)
      await loadVideoDevices()
    } catch (err) {
      handleApiError(err)
    }
  }

  function stopCamera() {
    if (scanTimerRef.current) window.clearInterval(scanTimerRef.current)
    scanTimerRef.current = null
    setIsScanning(false)
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) videoRef.current.srcObject = null
    setIsCameraOn(false)
  }

  async function captureAndRecognize() {
    if (!videoRef.current || !canvasRef.current || !recognitionSessionId || isRecognizing) return
    const video = videoRef.current
    if (!video.videoWidth || !video.videoHeight) return
    setIsRecognizing(true)
    try {
      const canvas = canvasRef.current
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height)
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.86))
      if (!blob) return
      if (latestFrameUrl) URL.revokeObjectURL(latestFrameUrl)
      setLatestFrameUrl(URL.createObjectURL(blob))
      const form = new FormData()
      form.append('file', blob, `frame-${Date.now()}.jpg`)
      form.append('session_id', recognitionSessionId)
      if (recognitionCameraId) form.append('camera_id', recognitionCameraId)
      const result = await api('/api/recognition/image', { method: 'POST', body: form })
      setDetections(result.detections || [])
      await Promise.all([loadAll(), loadRoster()])
    } catch (err) {
      handleApiError(err)
    } finally {
      setIsRecognizing(false)
    }
  }

  function startScanning() {
    if (!isCameraOn || !recognitionSessionId || isScanning) return
    setIsScanning(true)
    captureAndRecognize()
    scanTimerRef.current = window.setInterval(captureAndRecognize, 1800)
  }

  function stopScanning() {
    if (scanTimerRef.current) window.clearInterval(scanTimerRef.current)
    scanTimerRef.current = null
    setIsScanning(false)
  }

  async function markManual(student, statusValue = 'MANUAL') {
    if (!recognitionSessionId) return
    setBusy(true)
    setError('')
    try {
      await api('/api/attendance-logs/manual', {
        method: 'POST',
        body: JSON.stringify({
          session_id: Number(recognitionSessionId),
          student_id: student.id,
          camera_id: recognitionCameraId ? Number(recognitionCameraId) : null,
          status: statusValue,
          note: 'Giảng viên xác nhận thủ công tại trạm camera',
        }),
      })
      await Promise.all([loadAll(), loadRoster()])
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function confirmDetection(detection) {
    const eventId = detectionKey(detection)
    const studentId = detection.student_id || detection.student?.id
    if (!recognitionSessionId || !studentId) return
    setBusy(true)
    setError('')
    try {
      const result = await api('/api/recognition/confirm', {
        method: 'POST',
        body: JSON.stringify({
          recognition_event_id: eventId || null,
          session_id: Number(recognitionSessionId),
          student_id: Number(studentId),
          camera_id: recognitionCameraId ? Number(recognitionCameraId) : null,
        }),
      })
      setError(result.message || 'Đã xác nhận điểm danh.')
      if (result.confirmed) {
        setDetections((current) => current.map((item) => (
          detectionKey(item) === eventId ? { ...item, status: result.status, message: result.message, attendance_log: result.attendance_log } : item
        )))
        await Promise.all([loadAll(), loadRoster()])
      }
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  async function rejectDetection(detection) {
    const id = detectionKey(detection, `${detection.subject || detection.event?.subject}-${Date.now()}`)
    setBusy(true)
    setError('')
    try {
      if (detectionKey(detection)) {
        const result = await api(`/api/recognition/${detectionKey(detection)}/reject`, { method: 'POST' })
        setError(result.message || 'Đã bỏ qua kết quả nhận diện.')
      }
      setRejectedDetectionIds((current) => [...current, id])
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  function skipDetection(detection, index) {
    const id = detectionKey(detection, `${detection.subject || detection.event?.subject}-${index}`)
    setRejectedDetectionIds((current) => [...current, id])
  }

  async function loadStudentSummary(studentId = summaryStudentId) {
    if (!studentId) {
      setStudentSummary(null)
      return
    }
    setBusy(true)
    setError('')
    try {
      const result = await api(`/api/students/${studentId}/attendance-summary`)
      setStudentSummary(result)
    } catch (err) {
      handleApiError(err)
    } finally {
      setBusy(false)
    }
  }

  if (!auth.token) {
    return (
      <LoginScreen
        mode={authMode}
        onModeChange={(mode) => {
          setAuthMode(mode)
          setLoginError('')
        }}
        loginForm={loginForm}
        registerForm={registerForm}
        onLoginChange={(key, value) => setLoginForm((current) => ({ ...current, [key]: value }))}
        onRegisterChange={(key, value) => setRegisterForm((current) => ({ ...current, [key]: value }))}
        onLoginSubmit={handleLogin}
        onRegisterSubmit={handleRegisterTeacher}
        error={loginError || error}
        message={registerMessage}
        busy={busy}
      />
    )
  }

  const tabs = [
    ['directory', Users, 'Danh mục'],
    ['sessions', ClipboardList, 'Buổi điểm danh'],
    ['faces', ImageUp, 'Hồ sơ khuôn mặt'],
    ['recognition', Video, 'Trạm camera'],
    ['account', ShieldCheck, 'Tài khoản'],
  ]

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><CheckCircle2 size={22} /></div>
          <div><strong>FaceAttend</strong><span>Bảng điều khiển</span></div>
        </div>
        <nav>
          {tabs.map(([id, Icon, label]) => (
            <button key={id} className={activeTab === id ? 'active' : ''} onClick={() => setActiveTab(id)}>
              <Icon size={18} /><span>{label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <h1>Điểm danh khuôn mặt</h1>
            <p>Hệ thống điểm danh bằng camera, đối chiếu CompreFace với danh sách sinh viên trong lớp.</p>
          </div>
          <div className="topbar-actions">
            {auth.user ? (
              <div className="user-chip">
                <strong>{auth.user.full_name || auth.user.username}</strong>
                <span>{auth.user.role}</span>
              </div>
            ) : null}
            <StatusBar status={status} error={error} />
            <IconButton title="Làm mới" onClick={loadAll} disabled={busy}>
              {busy ? <Loader2 className="spin" size={18} /> : <RefreshCcw size={18} />}
            </IconButton>
            <IconButton title="Đăng xuất" onClick={handleLogout} disabled={busy}>
              <LogOut size={18} />
            </IconButton>
          </div>
        </header>

        {activeTab === 'directory' && (
          <div className="grid two">
            <Section icon={GraduationCap} title="Lớp học">
              {canManageCatalog ? <form className="form-grid" onSubmit={saveClass}>
                <Field label="Mã lớp"><input value={forms.class.class_code} onChange={(e) => updateForm('class', 'class_code', e.target.value)} required /></Field>
                <Field label="Tên lớp"><input value={forms.class.class_name} onChange={(e) => updateForm('class', 'class_name', e.target.value)} required /></Field>
                <Field label="Năm học"><input value={forms.class.school_year} onChange={(e) => updateForm('class', 'school_year', e.target.value)} /></Field>
                <button className="primary" type="submit">{editingClassId ? <Save size={17} /> : <CirclePlus size={17} />} {editingClassId ? 'Lưu lớp' : 'Thêm lớp'}</button>
                {editingClassId ? <button className="secondary" type="button" onClick={() => { setEditingClassId(null); setForms((current) => ({ ...current, class: emptyClass })) }}><X size={17} /> Hủy</button> : null}
              </form> : null}
              <DataTable rows={data.classes} emptyText="Chưa có lớp" columns={[
                { key: 'class_code', label: 'Mã' },
                { key: 'class_name', label: 'Tên lớp' },
                { key: 'school_year', label: 'Năm học' },
                { key: 'status', label: 'Trạng thái', render: (row) => <Pill tone={row.status === 'ACTIVE' ? 'ok' : 'neutral'}>{row.status}</Pill> },
                { key: 'actions', label: '', render: (row) => <div className="row-actions"><IconButton title="Xem sinh viên" onClick={() => loadClassDetail(row.id)}><Users size={16} /></IconButton>{canManageCatalog ? <><IconButton title="Sửa lớp" onClick={() => editClass(row)}><Pencil size={16} /></IconButton><IconButton title="Xóa lớp" onClick={() => deleteItem(`/api/classes/${row.id}`)}><Trash2 size={16} /></IconButton></> : null}</div> },
              ]} />
            </Section>

            <Section icon={Users} title="Sinh viên trong lớp">
              {classDetail ? (
                <div className="subject-status">
                  <strong>{classDetail.class_code}</strong>
                  <span>{classDetail.class_name}</span>
                  <strong>{classDetail.student_count}</strong>
                  <span>sinh viên</span>
                </div>
              ) : null}
              <DataTable rows={classDetail?.students || []} emptyText="Chọn một lớp để xem danh sách sinh viên" columns={[
                { key: 'student_code', label: 'Mã SV' },
                { key: 'full_name', label: 'Họ tên' },
                { key: 'cohort', label: 'Khóa' },
                { key: 'major', label: 'Ngành' },
                { key: 'compreface_subject', label: 'Subject', render: (row) => row.compreface_subject || 'Chưa map' },
                { key: 'face_profile_status', label: 'Hồ sơ khuôn mặt', render: (row) => row.has_face_profile ? <Pill tone="ok">{row.face_profile_status}</Pill> : <Pill tone="warn">Chưa có</Pill> },
              ]} />
            </Section>

            <Section icon={BookOpen} title="Môn học">
              {canManageCatalog ? <form className="form-grid" onSubmit={saveCourse}>
                <Field label="Mã môn"><input value={forms.course.course_code} onChange={(e) => updateForm('course', 'course_code', e.target.value)} required /></Field>
                <Field label="Tên môn"><input value={forms.course.course_name} onChange={(e) => updateForm('course', 'course_name', e.target.value)} required /></Field>
                <Field label="Tín chỉ"><input type="number" value={forms.course.credits} onChange={(e) => updateForm('course', 'credits', e.target.value)} /></Field>
                <button className="primary" type="submit">{editingCourseId ? <Save size={17} /> : <CirclePlus size={17} />} {editingCourseId ? 'Lưu môn' : 'Thêm môn'}</button>
                {editingCourseId ? <button className="secondary" type="button" onClick={() => { setEditingCourseId(null); setForms((current) => ({ ...current, course: emptyCourse })) }}><X size={17} /> Hủy</button> : null}
              </form> : null}
              <DataTable rows={data.courses} emptyText="Chưa có môn" columns={[
                { key: 'course_code', label: 'Mã' },
                { key: 'course_name', label: 'Tên môn' },
                { key: 'credits', label: 'TC' },
                { key: 'status', label: 'Trạng thái', render: (row) => <Pill tone={row.status === 'ACTIVE' ? 'ok' : 'neutral'}>{row.status}</Pill> },
                { key: 'actions', label: '', render: (row) => canManageCatalog ? <div className="row-actions"><IconButton title="Sửa môn" onClick={() => editCourse(row)}><Pencil size={16} /></IconButton><IconButton title="Xóa môn" onClick={() => deleteItem(`/api/courses/${row.id}`)}><Trash2 size={16} /></IconButton></div> : null },
              ]} />
            </Section>

            <Section icon={Users} title="Sinh viên">
              {canManageCatalog ? <form className="form-grid wide" onSubmit={(event) => {
                event.preventDefault()
                submitJson('/api/students', { ...forms.student, class_id: forms.student.class_id ? Number(forms.student.class_id) : null }, 'student', emptyStudent)
              }}>
                <Field label="Mã SV"><input value={forms.student.student_code} onChange={(e) => updateForm('student', 'student_code', e.target.value)} required /></Field>
                <Field label="Họ tên"><input value={forms.student.full_name} onChange={(e) => updateForm('student', 'full_name', e.target.value)} required /></Field>
                <Field label="Lớp"><select value={forms.student.class_id} onChange={(e) => updateForm('student', 'class_id', e.target.value)}><option value="">Không chọn</option>{data.classes.map((item) => <option key={item.id} value={item.id}>{item.class_code}</option>)}</select></Field>
                <Field label="Khóa học"><input value={forms.student.cohort} onChange={(e) => updateForm('student', 'cohort', e.target.value)} placeholder="VD: K66" /></Field>
                <Field label="Ngành"><input value={forms.student.major} onChange={(e) => updateForm('student', 'major', e.target.value)} placeholder="VD: CNTT" /></Field>
                <Field label="Email"><input value={forms.student.email} onChange={(e) => updateForm('student', 'email', e.target.value)} /></Field>
                <button className="primary" type="submit"><CirclePlus size={17} /> Thêm SV</button>
              </form> : null}
              <div className="filter-row"><Search size={17} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Tìm mã, tên, lớp" /></div>
              {canManageCatalog ? <div className="import-row">
                <input type="file" accept=".csv,text/csv" onChange={(e) => setStudentCsvFile(e.target.files?.[0] || null)} />
                <button className="secondary" type="button" onClick={importStudentsCsv} disabled={!studentCsvFile}>
                  <ImageUp size={17} /> Import CSV
                </button>
              </div> : null}
              <DataTable rows={filteredStudents} emptyText="Chưa có sinh viên" columns={[
                { key: 'student_code', label: 'Mã SV' },
                { key: 'full_name', label: 'Họ tên' },
                { key: 'class_name', label: 'Lớp' },
                { key: 'cohort', label: 'Khóa' },
                { key: 'major', label: 'Ngành' },
                { key: 'face_profile', label: 'Khuôn mặt', render: (row) => row.face_profile ? <Pill tone="ok">{row.face_profile.status}</Pill> : <Pill>Chưa có</Pill> },
              ]} />
            </Section>

            <Section icon={UserCheck} title="Trạng thái sinh viên">
              <div className="form-grid">
                <Field label="Sinh viên">
                  <select value={summaryStudentId} onChange={(e) => { setSummaryStudentId(e.target.value); loadStudentSummary(e.target.value) }}>
                    <option value="">Chọn sinh viên</option>
                    {data.students.map((item) => <option key={item.id} value={item.id}>{item.student_code} - {item.full_name}</option>)}
                  </select>
                </Field>
                <button className="secondary" type="button" onClick={() => loadStudentSummary()} disabled={!summaryStudentId}><RefreshCcw size={17} /> Cập nhật</button>
              </div>
              {studentSummary ? (
                <div className="student-summary">
                  <div><span>Họ tên</span><strong>{studentSummary.student.full_name}</strong></div>
                  <div><span>Mã SV</span><strong>{studentSummary.student.student_code}</strong></div>
                  <div><span>Lớp</span><strong>{studentSummary.student.class_name || 'Chưa có'}</strong></div>
                  <div><span>Khóa học</span><strong>{studentSummary.student.cohort || 'Chưa có'}</strong></div>
                  <div><span>Ngành</span><strong>{studentSummary.student.major || 'Chưa có'}</strong></div>
                  <div><span>Tổng buổi</span><strong>{studentSummary.total_sessions}</strong></div>
                  <div><span>Đã đi học</span><strong>{studentSummary.attended_sessions}</strong></div>
                  <div><span>Nghỉ</span><strong>{studentSummary.absent_sessions}</strong></div>
                  <div><span>Hồ sơ khuôn mặt</span><strong>{studentSummary.student.face_profile ? 'Đã map' : 'Chưa map'}</strong></div>
                </div>
              ) : <div className="empty-panel">Chọn sinh viên để xem trạng thái</div>}
            </Section>

            <Section icon={Camera} title="Camera trong hệ thống">
              {canManageCatalog ? <form className="form-grid" onSubmit={(event) => { event.preventDefault(); submitJson('/api/cameras', forms.camera, 'camera', emptyCamera) }}>
                <Field label="Mã camera"><input value={forms.camera.camera_code} onChange={(e) => updateForm('camera', 'camera_code', e.target.value)} required /></Field>
                <Field label="Tên"><input value={forms.camera.name} onChange={(e) => updateForm('camera', 'name', e.target.value)} required /></Field>
                <Field label="Vị trí"><input value={forms.camera.location} onChange={(e) => updateForm('camera', 'location', e.target.value)} /></Field>
                <Field label="Stream URL"><input value={forms.camera.stream_url} onChange={(e) => updateForm('camera', 'stream_url', e.target.value)} /></Field>
                <button className="primary" type="submit"><CirclePlus size={17} /> Thêm camera</button>
              </form> : null}
              <DataTable rows={data.cameras} emptyText="Chưa có camera" columns={[
                { key: 'camera_code', label: 'Mã' },
                { key: 'name', label: 'Tên' },
                { key: 'location', label: 'Vị trí' },
                { key: 'status', label: 'Trạng thái', render: (row) => <Pill tone="ok">{row.status}</Pill> },
              ]} />
            </Section>
          </div>
        )}

        {activeTab === 'sessions' && (
          <div className="grid two">
            <Section icon={BookOpen} title="Gán lớp - môn">
              {canManageCatalog ? <form className="form-grid" onSubmit={(event) => {
                event.preventDefault()
                submitJson('/api/class-courses', {
                  class_id: Number(forms.classCourse.class_id),
                  course_id: Number(forms.classCourse.course_id),
                  teacher_id: forms.classCourse.teacher_id ? Number(forms.classCourse.teacher_id) : null,
                  semester: forms.classCourse.semester,
                }, 'classCourse', emptyClassCourse)
              }}>
                <Field label="Lớp"><select value={forms.classCourse.class_id} onChange={(e) => updateForm('classCourse', 'class_id', e.target.value)} required><option value="">Chọn lớp</option>{data.classes.map((item) => <option key={item.id} value={item.id}>{item.class_code}</option>)}</select></Field>
                <Field label="Môn"><select value={forms.classCourse.course_id} onChange={(e) => updateForm('classCourse', 'course_id', e.target.value)} required><option value="">Chọn môn</option>{data.courses.map((item) => <option key={item.id} value={item.id}>{item.course_code}</option>)}</select></Field>
                <Field label="Giảng viên chính"><select value={forms.classCourse.teacher_id} onChange={(e) => updateForm('classCourse', 'teacher_id', e.target.value)}><option value="">Chưa phân công</option>{teacherUsers.filter((item) => item.status === 'ACTIVE').map((item) => <option key={item.id} value={item.id}>{item.full_name} - {item.email || item.username}</option>)}</select></Field>
                <Field label="Kỳ"><input value={forms.classCourse.semester} onChange={(e) => updateForm('classCourse', 'semester', e.target.value)} /></Field>
                <button className="primary" type="submit"><CirclePlus size={17} /> Gán</button>
              </form> : null}
              <DataTable rows={data.classCourses} emptyText="Chưa có lớp-môn" columns={[
                { key: 'class', label: 'Lớp', render: (row) => row.class?.class_code },
                { key: 'course', label: 'Môn', render: (row) => row.course?.course_code },
                { key: 'teacher_id', label: 'Giảng viên', render: (row) => teacherName(row.teacher_id) },
                { key: 'semester', label: 'Kỳ' },
                { key: 'status', label: 'Trạng thái', render: (row) => <Pill tone="ok">{row.status}</Pill> },
              ]} />
            </Section>

            <Section icon={ClipboardList} title="Buổi điểm danh">
              <form className="form-grid wide" onSubmit={(event) => {
                event.preventDefault()
                submitJson('/api/attendance-sessions', {
                  class_course_id: Number(forms.session.class_course_id),
                  session_name: forms.session.session_name,
                  start_time: toApiDatetime(forms.session.start_time),
                  late_threshold_minutes: Number(forms.session.late_threshold_minutes),
                }, 'session', { ...emptySession, start_time: toLocalDatetimeValue() })
              }}>
                <Field label="Lớp - môn"><select value={forms.session.class_course_id} onChange={(e) => updateForm('session', 'class_course_id', e.target.value)} required><option value="">Chọn</option>{data.classCourses.map((item) => <option key={item.id} value={item.id}>{item.class?.class_code} / {item.course?.course_code}</option>)}</select></Field>
                <Field label="Tên buổi"><input value={forms.session.session_name} onChange={(e) => updateForm('session', 'session_name', e.target.value)} required /></Field>
                <Field label="Bắt đầu"><input type="datetime-local" value={forms.session.start_time} onChange={(e) => updateForm('session', 'start_time', e.target.value)} required /></Field>
                <Field label="Tính muộn sau (phút)"><input type="number" value={forms.session.late_threshold_minutes} onChange={(e) => updateForm('session', 'late_threshold_minutes', e.target.value)} /></Field>
                <button className="primary" type="submit"><CirclePlus size={17} /> Tạo buổi</button>
              </form>
              <DataTable rows={data.sessions} emptyText="Chưa có buổi" columns={[
                { key: 'session_name', label: 'Buổi' },
                { key: 'class_name', label: 'Lớp', render: (row) => row.class_code || row.class_name || row.class_course?.class?.class_code },
                { key: 'course_name', label: 'Môn', render: (row) => row.course_code || row.course_name || row.class_course?.course?.course_code },
                { key: 'start_time', label: 'Bắt đầu', render: (row) => new Date(row.start_time).toLocaleString() },
                { key: 'status', label: 'Trạng thái', render: (row) => <Pill tone={row.status === 'OPEN' ? 'ok' : 'neutral'}>{row.status}</Pill> },
                { key: 'actions', label: '', render: (row) => (
                  <div className="row-actions">
                    {row.status !== 'OPEN' ? <IconButton title="Mở buổi điểm danh" onClick={() => openSession(row.id)}><Play size={16} /></IconButton> : null}
                    {row.status === 'OPEN' ? <IconButton title="Đóng buổi điểm danh" onClick={() => closeSession(row.id)}><Square size={16} /></IconButton> : null}
                  </div>
                ) },
              ]} />
            </Section>

            <Section icon={ClipboardList} title="Log điểm danh">
              <DataTable rows={data.logs} emptyText="Chưa có log" columns={[
                { key: 'student_name', label: 'Sinh viên' },
                { key: 'status', label: 'Trạng thái', render: (row) => <Pill tone={row.status === 'ON_TIME' ? 'ok' : 'warn'}>{row.status}</Pill> },
                { key: 'check_in_time', label: 'Thời gian', render: (row) => new Date(row.check_in_time).toLocaleString() },
              ]} />
            </Section>
          </div>
        )}

        {activeTab === 'faces' && (
          <div className="grid two">
            <Section icon={ImageUp} title="Gán hồ sơ khuôn mặt">
              <div className="subject-status">
                <span className={`dot ${data.comprefaceStatus?.status === 'ok' ? 'dot-ok' : 'dot-bad'}`} />
                <span>CompreFace {data.comprefaceStatus?.status || 'unknown'}</span>
                <strong>{data.comprefaceSubjects.length}</strong>
                <span>subject</span>
              </div>
              <div className="form-grid wide">
                <Field label="Sinh viên"><select value={selectedStudentId} onChange={(e) => setSelectedStudentId(e.target.value)}><option value="">Chọn sinh viên</option>{data.students.map((item) => <option key={item.id} value={item.id}>{item.student_code} - {item.full_name}</option>)}</select></Field>
                <Field label="Subject trên CompreFace">
                  <select value={selectedSubject} onChange={(e) => setSelectedSubject(e.target.value)}>
                    <option value="">Chọn subject hoặc tự tạo mới</option>
                    {data.comprefaceSubjects.map((subject) => <option key={subject} value={subject}>{subject}</option>)}
                  </select>
                </Field>
                <button className="primary" type="button" onClick={createFaceProfile}><CirclePlus size={17} /> Lưu hồ sơ</button>
              </div>
              <div className="note">Hồ sơ khuôn mặt dùng để nối subject trên CompreFace với sinh viên trong cơ sở dữ liệu. Khi camera nhận ra subject, backend dựa vào hồ sơ này để tìm tên, mã sinh viên, khóa học, ngành và kiểm tra sinh viên có thuộc lớp đang điểm danh hay không.</div>
            </Section>

            <Section icon={FileImage} title="Upload ảnh enroll">
              <div className="form-grid wide">
                <Field label="Ảnh khuôn mặt"><input type="file" multiple accept="image/*" onChange={(e) => setFaceFiles(Array.from(e.target.files || []))} /></Field>
                <button className="primary" type="button" onClick={uploadFaceImages} disabled={!selectedStudentId || faceFiles.length === 0}><ImageUp size={17} /> Upload {faceFiles.length || ''}</button>
              </div>
            </Section>

            <Section icon={Users} title="Trạng thái hồ sơ khuôn mặt">
              <DataTable rows={data.students} emptyText="Chưa có sinh viên" columns={[
                { key: 'student_code', label: 'Mã SV' },
                { key: 'full_name', label: 'Họ tên' },
                { key: 'class_name', label: 'Lớp' },
                { key: 'subject', label: 'Subject', render: (row) => row.face_profile?.compreface_subject || 'Chưa map' },
                { key: 'sample_count', label: 'Mẫu', render: (row) => row.face_profile?.sample_count || 0 },
                { key: 'status', label: 'Trạng thái', render: (row) => row.face_profile ? <Pill tone="ok">Đã map</Pill> : <Pill tone="warn">Chưa map</Pill> },
              ]} />
            </Section>
          </div>
        )}

        {activeTab === 'recognition' && (
          <div className="live-layout">
            <Section icon={Video} title="Trạm điểm danh">
              <div className="form-grid live-controls">
                <Field label="Buổi đang mở"><select value={recognitionSessionId} onChange={(e) => setRecognitionSessionId(e.target.value)} required><option value="">Chọn buổi</option>{openSessions.map((item) => <option key={item.id} value={item.id}>{item.session_name} - {item.class_code || 'Lớp'} / {item.course_code || 'Môn'}</option>)}</select></Field>
                <Field label="Camera hệ thống"><select value={recognitionCameraId} onChange={(e) => setRecognitionCameraId(e.target.value)}><option value="">Không chọn</option>{data.cameras.map((item) => <option key={item.id} value={item.id}>{item.camera_code} - {item.name}</option>)}</select></Field>
                <Field label="Camera đầu vào"><select value={selectedVideoDeviceId} onChange={(e) => setSelectedVideoDeviceId(e.target.value)}><option value="">Webcam mặc định</option>{videoDevices.map((device, index) => <option key={device.deviceId} value={device.deviceId}>{device.label || `Camera ${index + 1}`}</option>)}</select></Field>
              </div>
              <div className="camera-stage">
                <video ref={videoRef} autoPlay muted playsInline />
                <canvas ref={canvasRef} hidden />
                {!isCameraOn ? <div className="camera-placeholder"><Camera size={34} /><span>Chưa bật camera</span></div> : null}
              </div>
              <div className="station-actions">
                <button className="primary" type="button" onClick={startCamera}><Camera size={17} /> Bật camera</button>
                <button className="secondary" type="button" onClick={stopCamera}><Square size={17} /> Tắt camera</button>
                <button className="primary" type="button" onClick={startScanning} disabled={!isCameraOn || !recognitionSessionId || isScanning}><Play size={17} /> Bắt đầu quét</button>
                <button className="secondary" type="button" onClick={stopScanning}><Square size={17} /> Dừng quét</button>
                <button className="secondary" type="button" onClick={captureAndRecognize} disabled={!isCameraOn || !recognitionSessionId || isRecognizing}>{isRecognizing ? <Loader2 className="spin" size={17} /> : <Video size={17} />} Quét 1 lần</button>
              </div>
            </Section>

            <Section icon={UserCheck} title="Danh sách sinh viên trong lớp">
              <div className="roster-summary">
                <div><strong>{presentCount}</strong><span>Đã điểm danh</span></div>
                <div><strong>{roster.length - presentCount}</strong><span>Chưa có mặt</span></div>
              </div>
              <DataTable rows={roster} emptyText="Chọn buổi đang mở để xem danh sách lớp" columns={[
                { key: 'student_code', label: 'Mã SV' },
                { key: 'full_name', label: 'Họ tên' },
                { key: 'cohort', label: 'Khóa' },
                { key: 'major', label: 'Ngành' },
                { key: 'attendance_status', label: 'Trạng thái', render: (row) => <Pill tone={row.attendance_status === 'ABSENT' ? 'warn' : 'ok'}>{row.attendance_status}</Pill> },
                { key: 'manual', label: '', render: (row) => row.attendance_status === 'ABSENT' ? <IconButton title="Giảng viên xác nhận có mặt" onClick={() => markManual(row)}><UserCheck size={16} /></IconButton> : null },
              ]} />
            </Section>

            <Section icon={ClipboardList} title="Kết quả nhận diện gần nhất">
              {latestFrameUrl ? <img className="latest-frame" src={latestFrameUrl} alt="Khung hình camera gần nhất" /> : <div className="empty-panel">Chưa có khung hình</div>}
              <div className="detection-list">
                {detections.filter((item, index) => !rejectedDetectionIds.includes(detectionKey(item, `${item.subject || item.event?.subject}-${index}`))).length === 0 ? <div className="empty-panel">Chưa có nhận diện</div> : detections.filter((item, index) => !rejectedDetectionIds.includes(detectionKey(item, `${item.subject || item.event?.subject}-${index}`))).map((item, index) => {
                  const student = item.student
                  const statusLabel = DETECTION_STATUS_LABELS[item.status] || item.status || 'Cần kiểm tra'
                  return (
                    <div className="detection-row" key={detectionKey(item, index)}>
                      <div className="detection-top">
                        <div className="detection-main">
                          <strong>{item.student_name || student?.full_name || item.subject || item.event?.subject || 'Không xác định'}</strong>
                          <span>{item.student_code || student?.student_code || 'Chưa có mã sinh viên'}</span>
                        </div>
                        <Pill tone={detectionTone(item.status)}>{statusLabel}</Pill>
                        {item.belongs_to_session_class === true || item.in_class === true ? <CheckCircle2 size={16} className="ok-icon" /> : <AlertTriangle size={16} className="warn-icon" />}
                      </div>
                      <div className="detection-meta">
                        <div><span>Lớp</span><strong>{item.class_name || student?.class_name || 'Chưa xác định'}</strong></div>
                        <div><span>Khóa</span><strong>{student?.cohort || 'Chưa có'}</strong></div>
                        <div><span>Ngành</span><strong>{student?.major || 'Chưa có'}</strong></div>
                        <div><span>Môn học</span><strong>{item.course_name || 'Chưa có'}</strong></div>
                        <div><span>Subject</span><strong>{item.subject || item.event?.subject || 'Không có'}</strong></div>
                        <div><span>Similarity</span><strong>{formatSimilarity(item.similarity ?? item.event?.similarity)}</strong></div>
                      </div>
                      <p className="detection-message">{item.message || 'Cần giảng viên kiểm tra lại kết quả nhận diện.'}</p>
                      <div className="decision-actions">
                        {student || item.student_id ? <button className="primary compact" type="button" onClick={() => confirmDetection(item)} disabled={busy}>Đúng sinh viên này</button> : null}
                        <button className="secondary compact" type="button" onClick={() => rejectDetection(item)} disabled={busy}>Không phải sinh viên trong lớp</button>
                        <button className="secondary compact" type="button" onClick={() => skipDetection(item, index)}>Bỏ qua</button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </Section>
          </div>
        )}

        {activeTab === 'account' && (
          <div className="grid two">
            <Section icon={LockKeyhole} title="Đổi mật khẩu">
              <form className="form-grid" onSubmit={changePassword}>
                <Field label="Mật khẩu hiện tại">
                  <input type="password" value={passwordForm.old_password} onChange={(e) => setPasswordForm((current) => ({ ...current, old_password: e.target.value }))} autoComplete="current-password" required />
                </Field>
                <Field label="Mật khẩu mới">
                  <input type="password" value={passwordForm.new_password} onChange={(e) => setPasswordForm((current) => ({ ...current, new_password: e.target.value }))} autoComplete="new-password" required />
                </Field>
                <Field label="Nhập lại mật khẩu mới">
                  <input type="password" value={passwordForm.confirm_password} onChange={(e) => setPasswordForm((current) => ({ ...current, confirm_password: e.target.value }))} autoComplete="new-password" required />
                </Field>
                <button className="primary" type="submit" disabled={busy}><Save size={17} /> Lưu mật khẩu</button>
              </form>
              {passwordMessage ? <div className="success-panel">{passwordMessage}</div> : null}
            </Section>

            {isAdmin ? (
              <>
                <Section icon={UserPlus} title="Tài khoản giảng viên">
                  <div className="subject-status">
                    <strong>{pendingTeachers.length}</strong>
                    <span>tài khoản chờ duyệt</span>
                    <strong>{teacherUsers.length}</strong>
                    <span>giảng viên</span>
                  </div>
                  <DataTable rows={teacherUsers} emptyText="Chưa có tài khoản giảng viên" columns={[
                    { key: 'full_name', label: 'Họ tên' },
                    { key: 'email', label: 'Email trường', render: (row) => row.email || row.username },
                    { key: 'status', label: 'Trạng thái', render: (row) => <Pill tone={row.status === 'ACTIVE' ? 'ok' : row.status === 'PENDING' ? 'warn' : 'neutral'}>{row.status}</Pill> },
                    { key: 'last_login_at', label: 'Đăng nhập gần nhất', render: (row) => row.last_login_at ? new Date(row.last_login_at).toLocaleString() : 'Chưa có' },
                    { key: 'actions', label: '', render: (row) => (
                      <div className="row-actions">
                        {row.status === 'PENDING' ? <button className="primary compact" type="button" onClick={() => approveTeacher(row.id)} disabled={busy}>Duyệt</button> : null}
                        {row.status !== 'DISABLED' ? <button className="secondary compact" type="button" onClick={() => disableTeacher(row.id)} disabled={busy}>Khóa</button> : null}
                      </div>
                    ) },
                  ]} />
                </Section>

                <Section icon={ShieldCheck} title="Phân công lớp tín chỉ">
                  <form className="form-grid" onSubmit={createTeacherAssignment}>
                    <Field label="Giảng viên">
                      <select value={forms.teacherAssignment.teacher_id} onChange={(e) => updateForm('teacherAssignment', 'teacher_id', e.target.value)} required>
                        <option value="">Chọn giảng viên</option>
                        {teacherUsers.filter((item) => item.status === 'ACTIVE').map((item) => <option key={item.id} value={item.id}>{item.full_name} - {item.email || item.username}</option>)}
                      </select>
                    </Field>
                    <Field label="Lớp tín chỉ">
                      <select value={forms.teacherAssignment.class_course_id} onChange={(e) => updateForm('teacherAssignment', 'class_course_id', e.target.value)} required>
                        <option value="">Chọn lớp tín chỉ</option>
                        {data.classCourses.map((item) => <option key={item.id} value={item.id}>{classCourseLabel(item)}</option>)}
                      </select>
                    </Field>
                    <button className="primary" type="submit" disabled={busy}><UserCheck size={17} /> Gán giảng viên</button>
                  </form>
                  <DataTable rows={data.teacherAssignments} emptyText="Chưa có phân công bổ sung" columns={[
                    { key: 'teacher_id', label: 'Giảng viên', render: (row) => teacherName(row.teacher_id) },
                    { key: 'class_id', label: 'Lớp', render: (row) => studyClassName(row.class_id) },
                    { key: 'course_id', label: 'Môn', render: (row) => courseName(row.course_id) },
                    { key: 'semester', label: 'Kỳ' },
                    { key: 'created_at', label: 'Ngày tạo', render: (row) => new Date(row.created_at).toLocaleString() },
                  ]} />
                </Section>
              </>
            ) : (
              <Section icon={ShieldCheck} title="Phạm vi tài khoản">
                <div className="empty-panel">Giảng viên chỉ xem và điểm danh các lớp tín chỉ đã được admin phân công.</div>
              </Section>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
