import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
from datetime import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage



cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred,{
    'databaseURL': "https://face-recognition-11410814-default-rtdb.firebaseio.com/",
    'storageBucket': "face-recognition-11410814.appspot.com"
})

bucket=storage.bucket()




# webcap capture
cap=cv2.VideoCapture(0)
cap.set(3,640)
cap.set(4,480)


# backgroung image for webcam
imgBackground=cv2.imread("Resources/background.png")

# importing mode images iunto list
folderModePath="Resources/Modes"
modePathList=os.listdir(folderModePath)
imgModeList=[]
#print(modePathList)
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath,path)))
    
#print(len(imgModeList))



# load encoding file
print("Loading Encoding File")
file=open("EncodeFile.pickle","rb")
encodeListKnownWithIDs=pickle.load(file)
file.close()
encodeListKnown,studentIDs=encodeListKnownWithIDs
#print(encodeListKnown,studentIDs)
print("Encoding File Loaded")


# background image mode
modeType=3
counter=0
id=-1
imgStudent=[]

while True:
    success,img=cap.read()
    
    imgS=cv2.resize(img,(0,0),None,0.25,0.25)
    imgS=cv2.cvtColor(imgS,cv2.COLOR_BGR2RGB)
    
    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)
    
    imgBackground[162:162+480,55:55+640]=img
    imgBackground[44:44+633,808:808+414]=imgModeList[modeType]
    
    if faceCurFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            # print("matches", matches)
            # print("faceDis", faceDis)
        
            matchIndex = np.argmin(faceDis)
            print("Match Index", matchIndex)
        
            if matches[matchIndex]:
                # print("Tujhe PahChan Liya!")
                # print(studentIDs[matchIndex])
                
                # adding rectangle around face
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4
                bbox=55+x1, 162+y1, x2-x1, y2-y1
                # cv2.rectangle(imgBackground, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), (255, 0, 255), 2)    
                imgBackground=cvzone.cornerRect(imgBackground,bbox,20,rt=0)    
                id=studentIDs[matchIndex]
        

                if counter == 0:
                    # cvzone.putTextRect(imgBackground,"Loading...",(275,400))
                    # cv2.imshow("Face Attendance",imgBackground)
                    # cv2.waitKey(1)
                    counter = 1
                    modeType=2
                    
        if counter != 0:
            
            if counter ==1:
                studentInfo = db.reference(f'Students/{id}').get()
                print(studentInfo)
                
                # getting image from firebase
                blob=bucket.blob("Images/"+str(id)+".png")
                array=np.frombuffer(blob.download_as_string(),np.uint8)
                imgStudent=cv2.imdecode(array,cv2.COLOR_BGRA2BGR)
                
                # updating attendance
                
                datatimeObject=datetime.strptime(studentInfo["last_attendance_time"],"%Y-%m-%d %H:%M:%S")
                secondsEclased=(datetime.now()- datatimeObject).total_seconds()
                print(secondsEclased)
                if secondsEclased > 30:
                    ref=db.reference(f'Students/{id}')
                    studentInfo["Total_Attendance"] += 1
                    ref.child("Total_Attendance").set(studentInfo["Total_Attendance"])
                    ref.child("Total_Attendance_time").set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    modeType=4
                    counter=0
                    imgBackground[44:44+633,808:808+414]=imgModeList[modeType]
                
            
            if modeType != 0:
                
            
            
                if 10 <counter <20:    
                    modeType=1
                
                imgBackground[44:44+633,808:808+414]=imgModeList[modeType]
                
                
                
                
                    
                if counter <= 10:
                    cv2.putText(imgBackground,str(studentInfo["Total_Attendance"]),(861,125),cv2.FONT_HERSHEY_COMPLEX,1,(255,255,255),1)
                
                    cv2.putText(imgBackground,str(studentInfo["Major"]),(1006,550),cv2.FONT_HERSHEY_COMPLEX,0.5,(255,255,255),1)
                    cv2.putText(imgBackground,str(id),(1006,493),cv2.FONT_HERSHEY_COMPLEX,0.5,(255,255,255),1)
                           
                    #cv2.putText(imgBackground,str(studentInfo["Section"]),(1025,625),cv2.FONT_HERSHEY_COMPLEX,0.6,(100,100,100),1)
                    cv2.putText(imgBackground,str(studentInfo["Year"]),(1025,625),cv2.FONT_HERSHEY_COMPLEX,0.6,(100,100,100),1)
                    cv2.putText(imgBackground,str(studentInfo["RollNo"]),(1125,625),cv2.FONT_HERSHEY_COMPLEX,0.6,(100,100,100),1)
                
                    (w,h),_=cv2.getTextSize(str(studentInfo["Name"]),cv2.FONT_HERSHEY_COMPLEX,1,1)
                    offset=(414-w)//2
                    cv2.putText(imgBackground,str(studentInfo["Name"]),(808+offset,445),cv2.FONT_HERSHEY_COMPLEX,1,(50,50,50),2)    
                
                    imgBackground[175:175+216,909:909+216]=imgStudent
            
            
                counter += 1
            

            
            # reseting background image
                if counter >= 20:
                    counter=0
                    modeType=3
                    studentInfo=[]
                    imgStudent=[]
                    imgBackground[44:44+633,808:808+414]=imgModeList[modeType]
            
            
            
    else:
        modeType=3
        counter=0
    
    
    #cv2.imshow("Image",img)
    cv2.imshow("Face Attendance",imgBackground)
    if cv2.waitKey(1) & 0xFF ==ord('q'):
        break












cap.release()
cv2.destroyAllWindows()