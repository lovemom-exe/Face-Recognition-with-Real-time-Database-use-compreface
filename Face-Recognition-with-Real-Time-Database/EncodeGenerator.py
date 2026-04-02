import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage



cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred,{
    'databaseURL': "https://face-recognition-11410814-default-rtdb.firebaseio.com/",
    'storageBucket': "face-recognition-11410814.appspot.com"
})



# importing student images

folderPath="Images"
pathList=os.listdir(folderPath)
imgList=[]
studentIDs=[]
for path in pathList:
    imgList.append(cv2.imread(os.path.join(folderPath,path)))
    #print(path)
    studentIDs.append(os.path.splitext(path)[0])
#print(studentIDs)

    fileName=f'{folderPath}/{path}'
    bucket=storage.bucket()
    blob=bucket.blob(fileName)
    blob.upload_from_filename(fileName)
    print("Image Uploaded")


# function to encode images 
def findEncodings(imgList):
    encodeList=[]
    for img in imgList:
        img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        encode=face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

print("Encoding Started")
encodeListKnown=findEncodings(imgList)
encodeListKnownWithIDs=[encodeListKnown,studentIDs]
print(encodeListKnownWithIDs)
print("Encoding Completed")


file=open("EncodeFile.pickle","wb")
pickle.dump(encodeListKnownWithIDs,file)
print("Encoding File Created")