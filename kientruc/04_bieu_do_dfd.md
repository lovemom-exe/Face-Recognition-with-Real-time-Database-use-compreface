# Bieu do luong du lieu DFD

## 1. Quy uoc

| Ky hieu | Y nghia |
|---|---|
| Hinh tron/bo goc | Tien trinh xu ly |
| Hinh chu nhat | Tac nhan ngoai |
| Hinh tru/cylinder | Kho du lieu |
| Mui ten | Luong du lieu |

## 2. DFD muc ngu canh

```mermaid
flowchart LR
    Student["Sinh vien"] -->|Khuon mat truc tiep| System(("He thong quan ly diem danh\nbang nhan dien khuon mat"))
    Teacher["Giao vien/Quan tri vien"] -->|Thong tin lop, sinh vien, buoi hoc| System
    Camera["Camera/Webcam"] -->|Frame hinh anh| System
    System -->|Ket qua diem danh, bao cao| Teacher
    System -->|Trang thai da diem danh| Student
    System -->|Anh can nhan dien| AI["CompreFace AI Service"]
    AI -->|Subject, similarity, bounding box| System
```

## 3. DFD muc 0

```mermaid
flowchart LR
    Teacher["Giao vien/Quan tri vien"]
    Student["Sinh vien"]
    Camera["Camera/Webcam"]
    AI["CompreFace AI Service"]

    P1(("P1\nQuan ly danh muc"))
    P2(("P2\nQuan ly khuon mat"))
    P3(("P3\nNhan dien realtime"))
    P4(("P4\nXu ly diem danh"))
    P5(("P5\nTra cuu bao cao"))

    D1[("D1 Sinh vien/Lop")]
    D2[("D2 Ho so khuon mat")]
    D3[("D3 Buoi hoc")]
    D4[("D4 Su kien nhan dien")]
    D5[("D5 Log diem danh")]

    Teacher -->|Thong tin sinh vien, lop, mon| P1
    P1 -->|Ghi/cap nhat danh muc| D1
    P1 -->|Thong tin buoi hoc| D3

    Teacher -->|Anh mau, yeu cau enroll| P2
    P2 -->|Tao subject/upload anh| AI
    AI -->|Ket qua enroll| P2
    P2 -->|Metadata ho so khuon mat| D2

    Camera -->|Frame hinh anh| P3
    P3 -->|Anh JPG| AI
    AI -->|Subject, similarity, box| P3
    P3 -->|Su kien nhan dien| D4
    P3 -->|Ket qua hop le| P4

    Student -->|Co mat truoc camera| Camera
    P4 -->|Doc sinh vien| D1
    P4 -->|Doc buoi hoc active| D3
    P4 -->|Doc log gan nhat| D5
    P4 -->|Ghi log diem danh| D5

    Teacher -->|Yeu cau xem bao cao| P5
    P5 -->|Doc danh muc| D1
    P5 -->|Doc buoi hoc| D3
    P5 -->|Doc log| D5
    P5 -->|Bao cao diem danh| Teacher
```

## 4. DFD muc 1 cho tien trinh P3/P4: nhan dien va ghi diem danh

```mermaid
flowchart TB
    Camera["Camera/Webcam"]
    UI["Ung dung tram diem danh"]
    AI["CompreFace AI Service"]

    P31(("P3.1\nLay frame camera"))
    P32(("P3.2\nNen frame thanh JPG"))
    P33(("P3.3\nGui frame den AI"))
    P34(("P3.4\nLoc ket qua nhan dien"))
    P41(("P4.1\nTra cuu sinh vien"))
    P42(("P4.2\nKiem tra dedup"))
    P43(("P4.3\nTinh trang thai"))
    P44(("P4.4\nGhi log diem danh"))
    P45(("P4.5\nCap nhat giao dien"))

    D1[("D1 Sinh vien")]
    D3[("D3 Buoi hoc")]
    D4[("D4 Su kien nhan dien")]
    D5[("D5 Log diem danh")]

    Camera -->|Raw frame| P31
    P31 -->|Frame moi nhat| UI
    UI -->|Frame dinh ky| P32
    P32 -->|File JPG| P33
    P33 -->|HTTP POST image| AI
    AI -->|Subject, similarity, box| P34
    P34 -->|Luu event raw/unknown| D4
    P34 -->|Subject hop nguong| P41
    P41 -->|Tim theo compreface_name| D1
    D1 -->|Student| P41
    P41 -->|Student hop le| P42
    P42 -->|Kiem tra log gan nhat| D5
    D5 -->|Log gan nhat| P42
    P42 -->|Cho phep ghi| P43
    P43 -->|Doc buoi hoc active| D3
    D3 -->|Start time, late threshold| P43
    P43 -->|ON_TIME/LATE| P44
    P44 -->|Attendance log| D5
    P44 -->|Ket qua ghi nhan| P45
    P45 -->|Box, ten, trang thai| UI
```

## 5. DFD muc 1 cho quan ly ho so khuon mat

```mermaid
flowchart TB
    Admin["Quan tri vien"]
    AI["CompreFace AI Service"]
    P21(("P2.1\nNhap thong tin sinh vien"))
    P22(("P2.2\nTao subject"))
    P23(("P2.3\nThu thap anh mau"))
    P24(("P2.4\nKiem tra chat luong anh"))
    P25(("P2.5\nUpload/enroll anh"))
    P26(("P2.6\nXac nhan ho so active"))
    D1[("D1 Sinh vien")]
    D2[("D2 Ho so khuon mat")]

    Admin -->|Ho ten, ma SV, lop| P21
    P21 -->|Sinh vien moi| D1
    P21 -->|compreface_name| P22
    P22 -->|Create subject| AI
    AI -->|Subject created| P22
    Admin -->|Anh mau| P23
    P23 -->|Anh dau vao| P24
    P24 -->|Anh dat chat luong| P25
    P24 -->|Anh loi| Admin
    P25 -->|Upload image| AI
    AI -->|Enroll result| P26
    P26 -->|Trang thai ACTIVE/PENDING| D2
    P26 -->|Thong bao ket qua| Admin
```

## 6. Luong du lieu chinh

| Luong du lieu | Nguon | Dich | Noi dung |
|---|---|---|---|
| Frame hinh anh | Camera | Ung dung | Anh raw tu webcam |
| Goi nhan dien | Ung dung | CompreFace | Anh JPG + API key |
| Ket qua nhan dien | CompreFace | Ung dung | Subject, similarity, bounding box |
| Du lieu sinh vien | Quan tri vien | DB | Ho ten, lop, subject |
| Ban ghi diem danh | Service | DB | Student, session, time, status, similarity |
| Bao cao | DB | Giao vien | Danh sach co mat/muon/vang, thong ke |
