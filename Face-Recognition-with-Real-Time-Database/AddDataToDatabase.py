import firebase_admin
from firebase_admin import credentials
from firebase_admin import db



cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred,{
    'databaseURL': "https://face-recognition-11410814-default-rtdb.firebaseio.com/"
})


ref=db.reference('Students')

data={
    "1129":
    {
        "Name":"Faisal",
        "RollNo":11,
        "Major":"Politics",
        "Year":3,
        "Section":"3B",
        "Total_Attendance":30,
        "last_attendance_time":"2023-12-21 00:54:34"
    },
    
    "271223":
    {
        "Name":"Govind Yadav",
        "RollNo":27,
        "Major":"Android Development",
        "Year":3,
        "Section":"3B",
        "Total_Attendance":3,
        "last_attendance_time":"2023-12-21 00:54:34"
    },
    
    "321654":
    {
        "Name":"Murtaza Hussain",
        "RollNo":32,
        "Major":"Rbotics",
        "Year":10,
        "Section":"X",
        "Total_Attendance":300,
        "last_attendance_time":"2023-12-21 00:54:34"
    },
    
    "852741":
    {
        "Name":"Emily Blunt",
        "RollNo":85,
        "Major":"Economics",
        "Year":10,
        "Section":"X",
        "Total_Attendance":299,
        "last_attendance_time":"2023-12-21 00:54:34"
    },
    
    "963852":
    {
        "Name":"Elon Musk",
        "RollNo":69,
        "Major":"Entrepreneurship",
        "Year":15,
        "Section":"Y",
        "Total_Attendance":300,
        "last_attendance_time":"2023-12-21 00:54:34"
    },
    
    "08092006":
    {
        "Name":"Pranav Rai", 
        "RollNo":1129,
        "Major":"Web Development",
        "Year":3,
        "Section":"3C",
        "Total_Attendance":20,
        "last_attendance_time":"2023-12-21 00:54:34"
    },
    
    "11410814":
    {
        "Name":"Ahmad Raza",
        "RollNo":132,
        "Major":"Data Science",
        "Year":3,
        "Section":"3C",
        "Total_Attendance":10,
        "last_attendance_time":"2023-12-21 00:54:34"
    }
    
}


for key, value in data.items():
    ref.child(key).set(value)
    print("Data Added")