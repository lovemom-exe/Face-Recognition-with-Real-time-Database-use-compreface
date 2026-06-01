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
  Loader2,
  Pencil,
  Play,
  RefreshCcw,
  Save,
  Search,
  Square,
  Trash2,
  UserCheck,
  Users,
  Video,
  X,
} from 'lucide-react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8080'

const emptyClass = { class_code: '', class_name: '', school_year: '2026' }
const emptyCourse = { course_code: '', course_name: '', credits: 3 }
const emptyStudent = { student_code: '', full_name: '', class_id: '', email: '', cohort: '', major: '' }
const emptyCamera = { camera_code: '', name: '', location: '', stream_url: '' }
const emptyClassCourse = { class_id: '', course_id: '', semester: '2026-2' }
const emptySession = { class_course_id: '', session_name: '', start_time: '', late_threshold_minutes: 15 }

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: options.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
    ...options,
  })
  const text = await response.text()
  const data = text ? JSON.parse(text) : null
  if (!response.ok) throw new Error(data?.detail || `HTTP ${response.status}`)
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
    comprefaceSubjects: [],
    comprefaceStatus: null,
  })
  const [forms, setForms] = useState({
    class: emptyClass,
    course: emptyCourse,
    student: emptyStudent,
    camera: emptyCamera,
    classCourse: emptyClassCourse,
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

  const filteredStudents = useMemo(() => {
    const value = search.trim().toLowerCase()
    if (!value) return data.students
    return data.students.filter((student) => `${student.student_code} ${student.full_name} ${student.class_name || ''}`.toLowerCase().includes(value))
  }, [data.students, search])

  const openSessions = data.sessions.filter((session) => session.status === 'OPEN')
  const presentCount = roster.filter((student) => student.attendance_status !== 'ABSENT').length

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
      setStatus(health?.status === 'ok' ? 'ok' : 'error')
      setData({
        classes,
        courses,
        students,
        cameras,
        classCourses,
        sessions,
        logs,
        comprefaceSubjects: comprefaceSubjects.subjects || [],
        comprefaceStatus,
      })
      if (selectedClassId) {
        const detail = await api(`/api/classes/${selectedClassId}`)
        setClassDetail(detail)
      }
    } catch (err) {
      setStatus('error')
      setError(err.message)
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
      setError(err.message)
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
      setError(err.message)
    }
  }

  async function loadVideoDevices() {
    if (!navigator.mediaDevices?.enumerateDevices) return
    const devices = await navigator.mediaDevices.enumerateDevices()
    setVideoDevices(devices.filter((device) => device.kind === 'videoinput'))
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadAll()
      loadVideoDevices()
    }, 0)
    return () => {
      window.clearTimeout(timer)
      stopCamera()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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
      setError(err.message)
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
      setError(err.message)
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
      setError(err.message)
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
      setError(err.message)
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
      setError(err.message)
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
      setError(err.message)
    } finally {
      setBusy(false)
    }
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
      setError(err.message)
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
      setError(err.message)
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
      setError(err.message)
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
      setError(err.message)
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
      setError(err.message)
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
      setError(err.message)
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
      setError(err.message)
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
      setError(err.message)
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
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const tabs = [
    ['directory', Users, 'Danh mục'],
    ['sessions', ClipboardList, 'Buổi điểm danh'],
    ['faces', ImageUp, 'Hồ sơ khuôn mặt'],
    ['recognition', Video, 'Trạm camera'],
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
            <StatusBar status={status} error={error} />
            <IconButton title="Làm mới" onClick={loadAll} disabled={busy}>
              {busy ? <Loader2 className="spin" size={18} /> : <RefreshCcw size={18} />}
            </IconButton>
          </div>
        </header>

        {activeTab === 'directory' && (
          <div className="grid two">
            <Section icon={GraduationCap} title="Lớp học">
              <form className="form-grid" onSubmit={saveClass}>
                <Field label="Mã lớp"><input value={forms.class.class_code} onChange={(e) => updateForm('class', 'class_code', e.target.value)} required /></Field>
                <Field label="Tên lớp"><input value={forms.class.class_name} onChange={(e) => updateForm('class', 'class_name', e.target.value)} required /></Field>
                <Field label="Năm học"><input value={forms.class.school_year} onChange={(e) => updateForm('class', 'school_year', e.target.value)} /></Field>
                <button className="primary" type="submit">{editingClassId ? <Save size={17} /> : <CirclePlus size={17} />} {editingClassId ? 'Lưu lớp' : 'Thêm lớp'}</button>
                {editingClassId ? <button className="secondary" type="button" onClick={() => { setEditingClassId(null); setForms((current) => ({ ...current, class: emptyClass })) }}><X size={17} /> Hủy</button> : null}
              </form>
              <DataTable rows={data.classes} emptyText="Chưa có lớp" columns={[
                { key: 'class_code', label: 'Mã' },
                { key: 'class_name', label: 'Tên lớp' },
                { key: 'school_year', label: 'Năm học' },
                { key: 'status', label: 'Trạng thái', render: (row) => <Pill tone={row.status === 'ACTIVE' ? 'ok' : 'neutral'}>{row.status}</Pill> },
                { key: 'actions', label: '', render: (row) => <div className="row-actions"><IconButton title="Xem sinh viên" onClick={() => loadClassDetail(row.id)}><Users size={16} /></IconButton><IconButton title="Sửa lớp" onClick={() => editClass(row)}><Pencil size={16} /></IconButton><IconButton title="Xóa lớp" onClick={() => deleteItem(`/api/classes/${row.id}`)}><Trash2 size={16} /></IconButton></div> },
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
              <form className="form-grid" onSubmit={saveCourse}>
                <Field label="Mã môn"><input value={forms.course.course_code} onChange={(e) => updateForm('course', 'course_code', e.target.value)} required /></Field>
                <Field label="Tên môn"><input value={forms.course.course_name} onChange={(e) => updateForm('course', 'course_name', e.target.value)} required /></Field>
                <Field label="Tín chỉ"><input type="number" value={forms.course.credits} onChange={(e) => updateForm('course', 'credits', e.target.value)} /></Field>
                <button className="primary" type="submit">{editingCourseId ? <Save size={17} /> : <CirclePlus size={17} />} {editingCourseId ? 'Lưu môn' : 'Thêm môn'}</button>
                {editingCourseId ? <button className="secondary" type="button" onClick={() => { setEditingCourseId(null); setForms((current) => ({ ...current, course: emptyCourse })) }}><X size={17} /> Hủy</button> : null}
              </form>
              <DataTable rows={data.courses} emptyText="Chưa có môn" columns={[
                { key: 'course_code', label: 'Mã' },
                { key: 'course_name', label: 'Tên môn' },
                { key: 'credits', label: 'TC' },
                { key: 'status', label: 'Trạng thái', render: (row) => <Pill tone={row.status === 'ACTIVE' ? 'ok' : 'neutral'}>{row.status}</Pill> },
                { key: 'actions', label: '', render: (row) => <div className="row-actions"><IconButton title="Sửa môn" onClick={() => editCourse(row)}><Pencil size={16} /></IconButton><IconButton title="Xóa môn" onClick={() => deleteItem(`/api/courses/${row.id}`)}><Trash2 size={16} /></IconButton></div> },
              ]} />
            </Section>

            <Section icon={Users} title="Sinh viên">
              <form className="form-grid wide" onSubmit={(event) => {
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
              </form>
              <div className="filter-row"><Search size={17} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Tìm mã, tên, lớp" /></div>
              <div className="import-row">
                <input type="file" accept=".csv,text/csv" onChange={(e) => setStudentCsvFile(e.target.files?.[0] || null)} />
                <button className="secondary" type="button" onClick={importStudentsCsv} disabled={!studentCsvFile}>
                  <ImageUp size={17} /> Import CSV
                </button>
              </div>
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
              <form className="form-grid" onSubmit={(event) => { event.preventDefault(); submitJson('/api/cameras', forms.camera, 'camera', emptyCamera) }}>
                <Field label="Mã camera"><input value={forms.camera.camera_code} onChange={(e) => updateForm('camera', 'camera_code', e.target.value)} required /></Field>
                <Field label="Tên"><input value={forms.camera.name} onChange={(e) => updateForm('camera', 'name', e.target.value)} required /></Field>
                <Field label="Vị trí"><input value={forms.camera.location} onChange={(e) => updateForm('camera', 'location', e.target.value)} /></Field>
                <Field label="Stream URL"><input value={forms.camera.stream_url} onChange={(e) => updateForm('camera', 'stream_url', e.target.value)} /></Field>
                <button className="primary" type="submit"><CirclePlus size={17} /> Thêm camera</button>
              </form>
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
              <form className="form-grid" onSubmit={(event) => {
                event.preventDefault()
                submitJson('/api/class-courses', { class_id: Number(forms.classCourse.class_id), course_id: Number(forms.classCourse.course_id), semester: forms.classCourse.semester }, 'classCourse', emptyClassCourse)
              }}>
                <Field label="Lớp"><select value={forms.classCourse.class_id} onChange={(e) => updateForm('classCourse', 'class_id', e.target.value)} required><option value="">Chọn lớp</option>{data.classes.map((item) => <option key={item.id} value={item.id}>{item.class_code}</option>)}</select></Field>
                <Field label="Môn"><select value={forms.classCourse.course_id} onChange={(e) => updateForm('classCourse', 'course_id', e.target.value)} required><option value="">Chọn môn</option>{data.courses.map((item) => <option key={item.id} value={item.id}>{item.course_code}</option>)}</select></Field>
                <Field label="Kỳ"><input value={forms.classCourse.semester} onChange={(e) => updateForm('classCourse', 'semester', e.target.value)} /></Field>
                <button className="primary" type="submit"><CirclePlus size={17} /> Gán</button>
              </form>
              <DataTable rows={data.classCourses} emptyText="Chưa có lớp-môn" columns={[
                { key: 'class', label: 'Lớp', render: (row) => row.class?.class_code },
                { key: 'course', label: 'Môn', render: (row) => row.course?.course_code },
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
      </main>
    </div>
  )
}

export default App
