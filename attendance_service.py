import cv2
import time
import requests
from typing import List, Dict, Any, Optional
from database.crud import AttendanceCRUD

class AttendanceService:
    """
    Service chuyÃªn biá»‡t xá»­ lÃ½ pipeline nháº­n diá»‡n vÃ  Ä‘iá»ƒm danh.
    Bao gá»“m:
    1. Gá»­i áº£nh lÃªn CompreFace API.
    2. Lá»c káº¿t quáº£ (similarity > 0.97).
    3. TrÃ¡nh spam Ä‘iá»ƒm danh liÃªn tá»¥c trong N giÃ¢y (Debounce cache).
    4. Ghi nháº­n xuá»‘ng Database qua AttendanceCRUD.
    """

    def __init__(self, api_key: str, api_url: str, debounce_seconds: float = 5.0):
        """
        Khá»Ÿi táº¡o Attendance Service

        Args:
            api_key: KhÃ³a API cá»§a CompreFace (Recognition Service).
            api_url: URL API nháº­n diá»‡n cá»§a CompreFace.
            debounce_seconds: NgÆ°á»¡ng thá»i gian (giÃ¢y) chá»‘ng spam gá»­i DB.
        """
        self.api_key = api_key
        self.api_url = api_url
        self.debounce_seconds = debounce_seconds

        # Dictionary lÆ°u thá»i gian cuá»‘i cÃ¹ng ghi nháº­n cá»§a tá»«ng cÃ¡ nhÃ¢n Ä‘á»ƒ chá»‘ng spam DB
        # Cáº¥u trÃºc: {"tÃªn_compreface": timestamp}
        self.debounce_cache: Dict[str, float] = {}

    def process_frame(self, frame) -> List[Dict[str, Any]]:
        """
        Gá»­i frame lÃªn CompreFace vÃ  xá»­ lÃ½ attendance pipeline.

        Args:
            frame: áº¢nh numpy array (OpenCV).

        Returns:
            Danh sÃ¡ch cÃ¡c khuÃ´n máº·t ÄÃƒ NHáº¬N DIá»†N Há»¢P Lá»† (similarity > 0.97).
            Format Ä‘á»ƒ client_app.py cÃ³ thá»ƒ dÃ¹ng váº½ UI:
            [{ "name": "...", "similarity": 0.99, "box": { "x_min": ..., ... } }]
        """
        if frame is None:
            return []

        # NÃ©n áº£nh thÃ nh jpg Ä‘á»ƒ tá»‘i Æ°u bÄƒng thÃ´ng
        _, buffer = cv2.imencode('.jpg', frame)
        headers = {"x-api-key": self.api_key}

        try:
            # Gá»­i HTTP POST vá»›i TTL 2 giÃ¢y Ä‘á»ƒ khÃ´ng lÃ m lag app
            response = requests.post(
                self.api_url,
                headers=headers,
                files={'file': ('frame.jpg', buffer.tobytes(), 'image/jpeg')},
                timeout=2.0
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get('result', [])
                valid_faces = []

                # TrÃ­ch xuáº¥t káº¿t quáº£ nháº­n diá»‡n
                for face in results:
                    subjects = face.get('subjects', [])
                    if subjects:
                        best_match = subjects[0]
                        similarity = best_match.get('similarity', 0.0)

                        # Chá»‰ láº¥y nhá»¯ng trÆ°á»ng há»£p cÃ³ Ä‘á»™ tin cáº­y > 0.97
                        if similarity > 0.97:
                            subject_name = best_match.get('subject')

                            valid_faces.append({
                                'name': subject_name,
                                'similarity': similarity,
                                'box': face.get('box', {})
                            })

                            # Äi qua cÆ¡ cháº¿ Ä‘iá»ƒm danh (cÃ³ debounce)
                            self._log_student_attendance(subject_name, similarity)

                return valid_faces
            else:
                print(f"[SERVICE] Lá»—i tá»« API CompreFace: HTTP {response.status_code}")
                return []

        except requests.exceptions.RequestTimeout:
            print("[SERVICE] Timeout: CompreFace Server pháº£n há»“i quÃ¡ cháº­m.")
            return []
        except requests.exceptions.ConnectionError:
            print("[SERVICE] Lá»—i káº¿t ná»‘i: KhÃ´ng thá»ƒ káº¿t ná»‘i tá»›i CompreFace Server.")
            return []
        except Exception as e:
            print(f"[SERVICE] Lá»—i khÃ´ng xÃ¡c Ä‘á»‹nh khi gá»­i áº£nh: {e}")
            return []

    def _log_student_attendance(self, name: str, similarity: float):
        """
        Ghi nháº­n xuá»‘ng Database, kiá»ƒm tra Debounce 5s chá»‘ng ghi liÃªn tá»¥c.
        """
        current_time = time.time()

        # CÆ¡ cháº¿ Debounce: Bá» qua náº¿u thá»i gian chÆ°a Ä‘á»§ 5 giÃ¢y so vá»›i láº§n cuá»‘i
        if name in self.debounce_cache:
            last_seen_time = self.debounce_cache[name]
            if current_time - last_seen_time < self.debounce_seconds:
                # QuÃ¡ nhanh -> return Ä‘á»ƒ khÃ´ng spam database layer
                return

        try:
            # Gá»i hÃ m Database (Trong Model CRUD Ä‘Ã£ cÃ³ logic 5 phÃºt chá»‘ng Ä‘iá»ƒm danh láº·p)
            # HÃ m service nÃ y gá»i DB khi pass qua má»©c debounce in-memory
            log = AttendanceCRUD.log_attendance(
                compreface_name=name,
                similarity=similarity
            )

            if log:
                print(f"[SERVICE] -> ÄÃ£ trigger lÆ°u DB thÃ nh cÃ´ng cho {name}")

        except Exception as e:
            print(f"[SERVICE] Lá»—i khi lÆ°u database cho {name}: {e}")

        finally:
            # Cáº­p nháº­t má»‘c thá»i gian nháº­n diá»‡n cho name nÃ y
            # (dÃ¹ DB cÃ³ reject vÃ¬ vi pháº¡m dedup 5 phÃºt, ta cÅ©ng cáº§n cháº·n gá»i DB á»Ÿ RAM 5s tiáº¿p theo)
            self.debounce_cache[name] = current_time

    def clear_cache(self):
        """HÃ m dá»n dáº¹p bá»™ Ä‘á»‡m debounce (dÃ¹ng khi refresh phiÃªn lÃ m viá»‡c)"""
        self.debounce_cache.clear()
