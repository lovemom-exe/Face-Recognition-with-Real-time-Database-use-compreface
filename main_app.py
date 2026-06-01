import sys
import cv2
import numpy as np
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont

# Import service vÃ  crud
from attendance_service import AttendanceService
from database.crud import AttendanceCRUD

# -------------------------- CONFIG --------------------------
API_KEY = os.environ.get("COMPREFACE_RECOGNITION_API_KEY", "")
API_URL = "http://localhost:8000/api/v1/recognition/recognize"
# ------------------------------------------------------------


class RecognitionWorker(QThread):
    """
    Luá»“ng phá»¥ chuyÃªn xá»­ lÃ½ giao tiáº¿p nháº­n diá»‡n khuÃ´n máº·t (CompreFace).
    KhÃ´ng lÃ m block giao diá»‡n chÃ­nh.
    """
    # Signal phÃ¡t ra danh sÃ¡ch faces Ä‘á»ƒ váº½
    # Danh sÃ¡ch faces: [{'name': '...', 'similarity': ..., 'box': {...}}]
    finished_signal = pyqtSignal(list)

    def __init__(self, service: AttendanceService):
        super().__init__()
        self.service = service
        self.frame_to_process = None
        self.is_running = True

    def set_frame(self, frame):
        """HÃ m nÃ y nhÃ©t frame vÃ o Ä‘á»ƒ chuáº©n bá»‹ process"""
        if self.frame_to_process is None: # Chá»‰ nháº­n náº¿u Ä‘ang ráº£nh
            self.frame_to_process = frame

    def run(self):
        while self.is_running:
            if self.frame_to_process is not None:
                # Copy frame ra xá»­ lÃ½ an toÃ n
                frame_copy = self.frame_to_process.copy()
                self.frame_to_process = None # XÃ³a Ä‘á»ƒ sáºµn sÃ ng nháº­n frame tiáº¿p theo

                # Gá»i service Ä‘áº©y áº£nh
                faces = self.service.process_frame(frame_copy)
                self.finished_signal.emit(faces)
            else:
                self.msleep(10) # TrÃ¡nh Äƒn vÃ£ CPU náº¿u chÆ°a cÃ³ áº£nh


class CameraThread(QThread):
    """Luá»“ng phá»¥ chuyÃªn Ä‘á»c Webcam cá»±c nhanh"""
    frame_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.is_running = True

    def run(self):
        cap = cv2.VideoCapture(0)
        # Ã‰p pháº§n cá»©ng cháº¡y 60 FPS náº¿u há»— trá»£
        cap.set(cv2.CAP_PROP_FPS, 60)

        while self.is_running:
            ret, frame = cap.read()
            if ret:
                self.frame_signal.emit(frame)
            else:
                self.msleep(10)

        cap.release()

    def stop(self):
        self.is_running = False
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tráº¡m Äiá»ƒm Danh Tá»± Äá»™ng - BÃ¡ch Khoa")
        self.resize(1200, 700)

        # Service nháº­n diá»‡n
        self.attendance_service = AttendanceService(api_key=API_KEY, api_url=API_URL)

        # Biáº¿n chá»©a dá»¯ liá»‡u khuÃ´n máº·t hiá»‡n táº¡i Ä‘á»ƒ váº½ Box Ä‘Ã¨ lÃªn camera mÆ°á»£t mÃ 
        self.current_faces = []

        self.init_ui()
        self.init_threads()

        # Timer tá»± Ä‘á»™ng load láº¡i báº£ng Ä‘iá»ƒm danh sau má»—i 2s Ä‘á»ƒ cÃ³ dá»¯ liá»‡u Real-time
        self.table_timer = QTimer(self)
        self.table_timer.timeout.connect(self.load_attendance_data)
        self.table_timer.start(2000)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # ---- BÃŠN TRÃI: KHUNG CAMERA ----
        left_layout = QVBoxLayout()

        title_video = QLabel("ðŸ”´ CAMERA NHáº¬N DIá»†N")
        title_video.setFont(QFont("Arial", 16, QFont.Bold))
        title_video.setAlignment(Qt.AlignCenter)
        title_video.setStyleSheet("color: #d35400;")
        left_layout.addWidget(title_video)

        self.video_label = QLabel()
        self.video_label.setFixedSize(800, 600)
        self.video_label.setStyleSheet("background-color: black; border: 2px solid gray;")
        left_layout.addWidget(self.video_label)

        main_layout.addLayout(left_layout)

        # ---- BÃŠN PHáº¢I: DANH SÃCH ÄIá»‚M DANH ----
        right_layout = QVBoxLayout()

        title_table = QLabel("ðŸ“‹ DANH SÃCH ÄIá»‚M DANH HÃ”M NAY")
        title_table.setFont(QFont("Arial", 14, QFont.Bold))
        right_layout.addWidget(title_table)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Sinh ViÃªn", "Thá»i Gian", "Tráº¡ng ThÃ¡i"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        right_layout.addWidget(self.table)

        refresh_btn = QPushButton("Biá»ƒu máº«u thá»‘ng kÃª") # (Táº¡m Ä‘á»ƒ dÃ nh)
        right_layout.addWidget(refresh_btn)

        main_layout.addLayout(right_layout, stretch=1)

        # Load dá»¯ liá»‡u ban Ä‘áº§u
        self.load_attendance_data()

    def init_threads(self):
        # 1. Luá»“ng cháº¡y AI
        self.ai_worker = RecognitionWorker(self.attendance_service)
        self.ai_worker.finished_signal.connect(self.on_recognition_finished)
        self.ai_worker.start()

        # 2. Luá»“ng Camera liÃªn tá»¥c báº¯n áº£nh ra
        self.camera_thread = CameraThread()
        self.camera_thread.frame_signal.connect(self.process_raw_frame)
        self.camera_thread.start()

        # 3. Timer thá»‰nh thoáº£ng nhÃ©t áº£nh vÃ o AI (trÃ¡nh spam network, 500ms 1 láº§n)
        self.ai_timer = QTimer(self)
        self.ai_timer.timeout.connect(self.trigger_ai)
        self.ai_timer.start(500) # 0.5s phÃ¢n tÃ­ch 1 khung hÃ¬nh

        self.latest_frame = None

    def process_raw_frame(self, frame):
        """Xá»­ lÃ½ trÃªn MainThread: nháº­n frame thÃ´, váº½ box vÃ  Ä‘áº©y lÃªn UI"""
        self.latest_frame = frame.copy() # LÆ°u láº¡i Ä‘á»ƒ Timer AI kÃ©o Ä‘i

        # Váº½ cÃ¡c khuÃ´n máº·t hiá»‡n cÃ³ (tá»a Ä‘á»™ láº¥y tá»« láº§n nháº­n diá»‡n gáº§n nháº¥t)
        target_frame = frame.copy()

        for face in self.current_faces:
            box = face.get('box', {})
            x_min, y_min = box.get('x_min', 0), box.get('y_min', 0)
            x_max, y_max = box.get('x_max', 0), box.get('y_max', 0)
            name = face.get('name', 'Unknown')
            sim = face.get('similarity', 0.0)

            # Khung mÃ u xanh = ÄÃ£ nháº­n ra (sim > 0.97)
            color = (0, 255, 0)

            cv2.rectangle(target_frame, (x_min, y_min), (x_max, y_max), color, 2)
            cv2.putText(target_frame, f"{name} {sim*100:.1f}%", (x_min, y_min - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Äá»‹nh dáº¡ng Ä‘á»ƒ hiá»ƒn thá»‹ PyQt
        rgb_image = cv2.cvtColor(target_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w

        q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        # Scaled mÆ°á»£t vÃ  giá»¯ tá»· lá»‡
        pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(pixmap)

    def trigger_ai(self):
        """Timer gá»i hÃ m nÃ y: QuÄƒng frame cuá»‘i vÃ o Worker AI Ä‘á»ƒ xá»­ lÃ½ á»Ÿ Background"""
        if self.latest_frame is not None:
            self.ai_worker.set_frame(self.latest_frame)

    def on_recognition_finished(self, faces):
        """Nháº­n káº¿t quáº£ AI tá»« Background cáº­p nháº­t vÃ o biáº¿n váº½"""
        self.current_faces = faces

    def load_attendance_data(self):
        """Truy váº¥n CSDL (crud.py) Ä‘á»• vÃ o Báº£ng bÃªn pháº£i"""
        try:
            today_logs = AttendanceCRUD.get_logs_by_date(date=datetime.now())

            self.table.setRowCount(len(today_logs))
            for row, log in enumerate(today_logs):
                # ID
                self.table.setItem(row, 0, QTableWidgetItem(str(log.id)))

                # Sinh ViÃªn
                student_name = log.student.full_name if log.student else "XÃ³a/Unknown"
                self.table.setItem(row, 1, QTableWidgetItem(student_name))

                # Thá»i gian
                time_str = log.check_in_time.strftime("%H:%M:%S") if log.check_in_time else ""
                self.table.setItem(row, 2, QTableWidgetItem(time_str))

                # Tráº¡ng thÃ¡i
                status_text = "Há»£p lá»‡" if log.status == "ON_TIME" else "Äi muá»™n"
                status_item = QTableWidgetItem(status_text)
                if log.status == "ON_TIME":
                    status_item.setForeground(Qt.darkGreen)
                else:
                    status_item.setForeground(Qt.red)
                self.table.setItem(row, 3, status_item)

        except Exception as e:
            print("[UI] Lá»—i khi load dá»¯ liá»‡u báº£ng:", e)

    def closeEvent(self, event):
        """Dá»n dáº¹p luá»“ng khi táº¯t cá»­a sá»•"""
        self.camera_thread.stop()
        self.ai_worker.is_running = False
        self.ai_worker.wait()
        event.accept()

from database.db_config import init_db

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Khá»Ÿi táº¡o database (tá»± Ä‘á»™ng táº¡o file attendance.db vÃ  báº£ng náº¿u cháº¡y máº·c Ä‘á»‹nh SQLite)
    init_db()

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
