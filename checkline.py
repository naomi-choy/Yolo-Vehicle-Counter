import cv2
import numpy

'''
800
1120
1930
2310
'''
frame = cv2.imread('./2310.jpg')

line_color = (255,0,0)

p1 = (285, 300)
p2 = (585, 250)
p3 = (690, 490)
p4 = (140, 615)
cv2.line(frame, p1, p4, line_color, 3)
cv2.line(frame, p4, p3, line_color, 3)
cv2.line(frame, p3, p2, line_color, 3)
cv2.line(frame, p2, p1, line_color, 3)

p5 = (635,365)
p6 = p3
p7 = (750,340)
p8 = (885,425)
p9 = (885,305)
p10 = (1040,370)
p11 = (980,275)
p12 = (1155,325)

cv2.line(frame, p5, p7, line_color, 3)
cv2.line(frame, p6, p8, line_color, 3)
cv2.line(frame, p7, p8, line_color, 3)
cv2.line(frame, p7, p9, line_color, 3)
cv2.line(frame, p8, p10, line_color, 3)
cv2.line(frame, p9, p10, line_color, 3)
cv2.line(frame, p9, p11, line_color, 3)
cv2.line(frame, p10, p12, line_color, 3)
cv2.line(frame, p11, p12, line_color, 3)

		

cv2.imshow('1', frame)
cv2.waitKey(0)
# cv2.destroyAllWindows()