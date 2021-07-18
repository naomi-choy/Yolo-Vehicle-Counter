import cv2
import numpy as np
import time
import pyvirtualcam

cap = cv2.VideoCapture("./second_out2.avi")
if not cap.isOpened():
    print("Cannot open camera")
    exit()
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

vcam = pyvirtualcam.Camera(width=width, height=height, fps=30)

frame_counter = 0
while True:
    ret, frame = cap.read()
    frame_counter += 1
    if frame_counter == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        frame_counter = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # cv2.imshow('frame',img)

    vcam.send(img)
    vcam.sleep_until_next_frame()

    if cv2.waitKey(1) & 0xFF == ord('q'):
      break

cap.release()
vcam.close()