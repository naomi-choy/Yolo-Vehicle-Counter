import cv2
import os

videoStream = cv2.VideoCapture("C:/Users/roborn/Documents/Yolo-Vehicle-Counter/first-cut.mp4")
save_path = "C:/Users/roborn/Documents/Yolo-Vehicle-Counter/clip1/"

counter = 0

while True:
    (grabbed, frame) = videoStream.read()
    if not grabbed:
        print("not grabbed")
        break
    counter += 1
    # print(counter)
    # print(save_path)
    file_path = save_path + str(counter) + ".jpg"
    # print(file_path)
    cv2.imwrite(file_path, frame)

videoStream.release()
