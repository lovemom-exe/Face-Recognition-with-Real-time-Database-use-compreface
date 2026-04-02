import cv2
import tkinter as tk
from PIL import Image, ImageTk
import threading
import requests
import time

# --- CẤU HÌNH COMPREFACE SERVER ---
API_KEY = "3652ba37-14dc-4884-8be1-77a27f0022e9"
URL = "http://localhost:8000/api/v1/recognition/recognize"

class CompreFaceClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trạm Điểm Danh - Bách Khoa (CompreFace AI)")
        self.root.geometry("800x600")

        # Giao diện Video
        self.video_panel = tk.Label(self.root)
        self.video_panel.pack(padx=10, pady=10)

        # Trạng thái Điểm danh
        self.info_lbl = tk.Label(self.root, text="Đang chờ hệ thống AI khởi động...", font=("Helvetica", 16, "bold"), fg="blue")
        self.info_lbl.pack(pady=10)

        # Thiết lập Webcam
        self.vid = cv2.VideoCapture(0)
        # Lệnh ép phần cứng đọc 60 FPS (nếu Webcam hỗ trợ)
        self.vid.set(cv2.CAP_PROP_FPS, 60)
        
        self.video_running = True
        self.last_results = []
        self.current_frame = None
        
        # Chạy 1 luồng song song duy nhất cho Máy chủ AI
        self.ai_thread = threading.Thread(target=self.process_ai, daemon=True)
        self.ai_thread.start()
        
        # Gọi hàm vòng lặp Video ở Luồng chính (Tăng độ mượt mà Tkinter)
        self.update_video()

    def update_video(self):
        """Xử lý hiển thị Video mượt mà bằng cơ chế After Loop của chính Tkinter"""
        if not self.video_running:
            return
            
        ret, frame = self.vid.read()
        if ret:
                self.current_frame = frame.copy()
                
                # Vẽ hộp vuông từ dữ liệu của AI gửi về
                for face in self.last_results:
                    box = face.get('box', {})
                    x_min, y_min = box.get('x_min', 0), box.get('y_min', 0)
                    x_max, y_max = box.get('x_max', 0), box.get('y_max', 0)
                    
                    name = "UNKNOWN"
                    color = (0, 0, 255) # Đỏ mặc định (Chưa biết người này)
                    similarity = 0.0
                    
                    subjects = face.get('subjects', [])
                    if subjects:
                        best_match = subjects[0]
                        similarity = best_match.get('similarity', 0)
                        if similarity > 0.97: # Khắt khe hơn: 97% mới kết luận (Chống nhận diện nhầm người lạ)
                            name = best_match.get('subject', 'UNKNOWN')
                            color = (0, 255, 0) # Xanh lá (Đã nhận diện)
                            
                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)
                    
                    # Vẽ text tên & % chính xác
                    label_text = f"{name} ({similarity*100:.1f}%)" if name != "UNKNOWN" else name
                    cv2.putText(frame, label_text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                # Render lên Tkinter
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_panel.imgtk = imgtk
                self.video_panel.configure(image=imgtk)
                
        # Gọi lại hàm này sau 15ms (Tương đương ép chạy ~60 FPS mượt mà)
        self.root.after(15, self.update_video)

    def process_ai(self):
        """Luồng 2: Bơm ảnh từ Camera lên Server bằng giao thức POST (1 giây 2 tấm để chống Lag mạng)"""
        headers = {"x-api-key": API_KEY}
        
        while self.video_running:
            if self.current_frame is not None:
                frame = self.current_frame.copy()
                
                # Nén ảnh thành format JPG nhị phân
                _, buffer = cv2.imencode('.jpg', frame)
                
                try:
                    # Truyền POST dữ liệu file qua HTTP Network
                    response = requests.post(
                        URL, 
                        headers=headers, 
                        files={'file': ('frame.jpg', buffer.tobytes(), 'image/jpeg')},
                        timeout=2.0 
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.last_results = data.get('result', [])
                        
                        # Xử lý Text Trạng thái UI
                        if len(self.last_results) > 0:
                            faces_info = []
                            for f in self.last_results:
                                subj = f.get('subjects', [])
                                if subj and subj[0].get('similarity', 0) > 0.97:
                                    faces_info.append(subj[0].get('subject'))
                            
                            if faces_info:
                                self.root.after(0, self.update_info, f"Đã quét: {', '.join(faces_info)}", "green")
                            else:
                                self.root.after(0, self.update_info, "Phát hiện khuôn mặt Lạ", "red")
                        else:
                            self.root.after(0, self.update_info, "Không thấy khuôn mặt", "gray")
                except Exception as e:
                    print("Lỗi kết nối Server CompreFace:", e)
                    self.root.after(0, self.update_info, "Lỗi mất mạng Máy Chủ AI", "orange")
                    
            time.sleep(0.5) # Delay 0.5s: 1 giây chỉ truyền 2 ảnh lên Server (Network Throttling)

    def update_info(self, text, color):
        self.info_lbl.config(text=text, fg=color)

    def on_closing(self):
        self.video_running = False
        if self.vid.isOpened():
             self.vid.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CompreFaceClientApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
