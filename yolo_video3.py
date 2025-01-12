# import the necessary packages
import numpy as np
import imutils
import time
from scipy import spatial
import cv2
from input_retrieval import *

from shapely.geometry import Polygon 	# for IOU calculation

# All these classes will be counted as 'vehicles'
list_of_vehicles = ["bicycle", "car", "motorbike", "bus", "truck", "train"]
# Setting the threshold for the number of frames to search a vehicle for
FRAMES_BEFORE_CURRENT = 10
inputWidth, inputHeight = 416, 416

# Parse command line arguments and extract the values required
LABELS, weightsPath, configPath, inputVideoPath, outputVideoPath,\
	preDefinedConfidence, preDefinedThreshold, USE_GPU = parseCommandLineArguments()

# Initialize a list of colors to represent each possible class label
np.random.seed(42)
COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
	dtype="uint8")
# PURPOSE: Displays the vehicle count on the top-left corner of the frame
# PARAMETERS: Frame on which the count is displayed, the count number of vehicles
# RETURN: N/A


def displayVehicleCount(frame, vehicle_count):
	cv2.putText(
		frame,  # Image
		'Detected Vehicles: ' + str(vehicle_count),  # Label
		(20, 20),  # Position
		cv2.FONT_HERSHEY_SIMPLEX,  # Font
		0.8,  # Size
		(0, 0xFF, 0),  # Color
		2,  # Thickness
		cv2.FONT_HERSHEY_COMPLEX_SMALL,
		)

# PURPOSE: Determining if the box-mid point cross the line or are within the range of 5 units
# from the line
# PARAMETERS: X Mid-Point of the box, Y mid-point of the box, Coordinates of the line
# RETURN:
# - True if the midpoint of the box overlaps with the line within a threshold of 5 units
# - False if the midpoint of the box lies outside the line and threshold


def boxAndLineOverlap(x_mid_point, y_mid_point, line_coordinates):
	x1_line, y1_line, x2_line, y2_line = line_coordinates  # Unpacking

	if (x_mid_point >= x1_line and x_mid_point <= x2_line+5) and\
		(y_mid_point >= y1_line and y_mid_point <= y2_line+5):
		return True
	return False

# PURPOSE: Displaying the FPS of the detected video
# PARAMETERS: Start time of the frame, number of frames within the same second
# RETURN: New start time, new number of frames


def displayFPS(start_time, num_frames):
	current_time = int(time.time())
	if(current_time > start_time):
		os.system('clear')  # Equivalent of CTRL+L on the terminal
		print("FPS:", num_frames)
		num_frames = 0
		start_time = current_time
	return start_time, num_frames

# PURPOSE: Draw all the detection boxes with a green dot at the center
# RETURN: box


def markDetectionBoxes(idxs, boxes, classIDs, confidences, frame, pos, angle):
	box = []
	# ensure at least one detection exists
	if len(idxs) > 0:
		# loop over the indices we are keeping
		for i in idxs.flatten():
			# extract the bounding box coordinates
			(x, y) = (boxes[i][0], boxes[i][1])
			(w, h) = (boxes[i][2], boxes[i][3])
			# print (x,y,w,h)
			centre = (x + (w//2), y + (h//2))
			
			if w*h >= 35000: # only show relavent cars
				box.append([[x,y],[x+w,y],[x+w, y+h],[x, y+h]]) 
				color = [int(c) for c in COLORS[classIDs[i]]]
				cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
				text = "{}: {:.4f}".format(LABELS[classIDs[i]],
				confidences[i])
				cv2.putText(frame, text, (x, y - 5),
				cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
				# Draw a green dot in the middle of the box
				cv2.circle(frame, centre, 2, (0, 0xFF, 0), thickness=2)

	return box

# PURPOSE: Initializing the video writer with the output video path and the same number
# of fps, width and height as the source video 
# PARAMETERS: Width of the source video, Height of the source video, the video stream
# RETURN: The initialized video writer
def initializeVideoWriter(video_width, video_height, videoStream):
	# Getting the fps of the source video
	sourceVideofps = videoStream.get(cv2.CAP_PROP_FPS)
	# initialize our video writer
	fourcc = cv2.VideoWriter_fourcc(*"MJPG")
	return cv2.VideoWriter(outputVideoPath, fourcc, sourceVideofps,
		(video_width, video_height), True)

# PURPOSE: Identifying if the current box was present in the previous frames
# PARAMETERS: All the vehicular detections of the previous frames, 
#			the coordinates of the box of previous detections
# RETURN: True if the box was current box was present in the previous frames;
#		  False if the box was not present in the previous frames
def boxInPreviousFrames(previous_frame_detections, current_box, current_detections):
	centerX, centerY, width, height = current_box
	dist = np.inf #Initializing the minimum distance
	# Iterating through all the k-dimensional trees
	for i in range(FRAMES_BEFORE_CURRENT):
		coordinate_list = list(previous_frame_detections[i].keys())
		if len(coordinate_list) == 0: # When there are no detections in the previous frame
			continue
		# Finding the distance to the closest point and the index
		temp_dist, index = spatial.KDTree(coordinate_list).query([(centerX, centerY)])
		if (temp_dist < dist):
			dist = temp_dist
			frame_num = i
			coord = coordinate_list[index[0]]

	if (dist > (max(width, height)/2)):
		return False

	# Keeping the vehicle ID constant
	current_detections[(centerX, centerY)] = previous_frame_detections[frame_num][coord]
	return True

def count_vehicles(idxs, boxes, classIDs, vehicle_count, previous_frame_detections, frame):
	current_detections = {}
	# ensure at least one detection exists
	if len(idxs) > 0:
		# loop over the indices we are keeping
		for i in idxs.flatten():
			# extract the bounding box coordinates
			(x, y) = (boxes[i][0], boxes[i][1])
			(w, h) = (boxes[i][2], boxes[i][3])
			
			centerX = x + (w//2)
			centerY = y+ (h//2)

			# When the detection is in the list of vehicles, AND
			# it crosses the line AND
			# the ID of the detection is not present in the vehicles
			if (LABELS[classIDs[i]] in list_of_vehicles):
				current_detections[(centerX, centerY)] = vehicle_count 
				if (not boxInPreviousFrames(previous_frame_detections, (centerX, centerY, w, h), current_detections)):
					vehicle_count += 1
					# vehicle_crossed_line_flag += True
				# else: #ID assigning
					# Add the current detection mid-point of box to the list of detected items
				# Get the ID corresponding to the current detection

				ID = current_detections.get((centerX, centerY))
				# If there are two detections having the same ID due to being too close, 
				# then assign a new ID to current detection.
				if (list(current_detections.values()).count(ID) > 1):
					current_detections[(centerX, centerY)] = vehicle_count
					vehicle_count += 1 

				# Display the ID at the center of the box
				# cv2.putText(frame, str(ID), (centerX, centerY),\
				# 	cv2.FONT_HERSHEY_SIMPLEX, 0.5, [0,0,255], 2)

	return vehicle_count, current_detections

def draw_lot(frame, pos, angle):
	# for i in range (len(coord)-1):
	# 	cv2.line(img, coord[i], coord[i+1], (255, 0, 0), 5) # (start x,y) , (end x,y)
	# 	cv2.putText(img, str(i+1), coord[i], cv2.FONT_HERSHEY_SIMPLEX, 1, 
	# 					(255, 0, 0), 3, cv2.LINE_AA)

	# 	# cv2.line(img, coord[1], coord[2], (255, 0, 0), 5)
	# 	# cv2.putText(img, '2', (x2, y2), cv2.FONT_HERSHEY_SIMPLEX, 1, 
	# 	# 				(255, 0, 0), 3, cv2.LINE_AA)

	# 	# cv2.line(img, coord[2], coord[3], (255, 0, 0), 5)
	# 	# cv2.putText(img, '3', (x3, y3), cv2.FONT_HERSHEY_SIMPLEX, 1, 
	# 	# 				(255, 0, 0), 3, cv2.LINE_AA)

	# cv2.line(img, coord[-1], coord[0], (255, 0, 0), 5)
	# cv2.putText(img, str(len(coord)), coord[-1], cv2.FONT_HERSHEY_SIMPLEX, 1, 
	# 				(255, 0, 0), 3, cv2.LINE_AA)

	# # cv2.line(img, (x1_line, y1_line), (x2_line, y2_line), (0,255,0), 10)


	# TODO: optimisation of reinitialising lots
	# TODO: cv2.polygon
	lots = []
	line_color = (255,0,0)
	
	if pos == 0 and angle == 0:
		p1 = (313, 303)
		p2 = (500, 303)
		p3 = (250, 425)
		p4 = (55, 415)
		cv2.line(frame, p1, p2, line_color, 3)
		cv2.line(frame, p2, p3, line_color, 3)
		cv2.line(frame, p3, p4, line_color, 3)
		cv2.line(frame, p4, p1, line_color, 3)

		lots.append([p1,p2,p3,p4])

		p1 = (766, 270)
		p2 = (992, 257)
		p3 = (1151, 402)
		p4 = (721, 439)
		cv2.line(frame, p1, p4, line_color, 3)
		cv2.line(frame, p4, p3, line_color, 3)
		cv2.line(frame, p3, p2, line_color, 3)
		cv2.line(frame, p2, p1, line_color, 3)

		lots.append([p1,p2,p3,p4])
		
	elif pos == 0 and angle == 1: 
		p1 = (440, 200)
		p2 = (750, 257)
		p3 = (300, 295)
		p4 = (600, 340)
		p5 = (295, 490)
		cv2.line(frame, p3, p4, line_color, 3)
		cv2.line(frame, p5, p4, line_color, 3)
		cv2.line(frame, p4, p2, line_color, 3)
		cv2.line(frame, p1, p2, line_color, 3)
	
	elif pos == 1 and angle == 0:
		p1 = (250, 295)
		p2 = (480, 275)
		p3 = (430, 384)
		p4 = (110, 430)
		cv2.line(frame, p1, p4, line_color, 3)
		cv2.line(frame, p4, p3, line_color, 3)
		cv2.line(frame, p3, p2, line_color, 3)
		cv2.line(frame, p2, p1, line_color, 3)

		lots.append(p1,p2,p3,p4)

		p5 = (700, 255)
		p6 = (920, 250)
		p7 = (785, 400)
		p8 = (1130, 250)
		p9 = (1185, 410)
		cv2.line(frame, p3, p7, line_color, 3)
		cv2.line(frame, p7, p6, line_color, 3)
		cv2.line(frame, p6, p5, line_color, 3)
		cv2.line(frame, p5, p3, line_color, 3)
		cv2.line(frame, p7, p9, line_color, 3)
		cv2.line(frame, p6, p8, line_color, 3)
		cv2.line(frame, p9, p8, line_color, 3)

		lots.append([p3,p5,p6,p7])
		lots.append([p6,p7,p8,p6])
		
	elif pos == 1 and angle == 1:
		p1 = (285, 300)
		p2 = (585, 250)
		p3 = (690, 490)
		p4 = (140, 615) 
		cv2.line(frame, p1, p4, line_color, 3)
		cv2.line(frame, p4, p3, line_color, 3)
		cv2.line(frame, p3, p2, line_color, 3)
		cv2.line(frame, p2, p1, line_color, 3)

		lots.append([p1,p2,p3,p4])

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

		lots.append([p5,p6,p7,p8])
		lots.append([p7,p8,p9,p10])
		lots.append([p9,p10,p11,p12])
	
	return lots
		
def calculate_iou(box1, box2):
	poly_1 = Polygon(box1)
	poly_2 = Polygon(box2)
	iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area
	return iou

def pos_angle(num_frames):
	pos = -1
	angle = -1
	if num_frames >= 30*25 and num_frames <= 30*30:
		pos = 0
		angle = 0
	if num_frames >= 30*37 and num_frames <= 30*42:
		pos = 0
		angle = 1
	if num_frames >= 30*(60+4) and num_frames <= 30*(60+7):
		pos =  1
		angle = 0
	if num_frames >= 30*(60+14) and num_frames <= 30*(60+19)+15:
		pos = 1
		angle = 1

	# print("in function pos:", pos, angle)	
	return pos, angle

def drawViolationBoxes(boxes, lots):
	for box in boxes: 	# for each detection box
		print("box:", box)
		for lot in lots: 	# for each parking lot 
			# calculate overlap
			print("lot:", lot)
			iou = calculate_iou(box, lot)
			print("iou:", iou)
			if iou < 0.15:
				continue
			elif iou < 0.3:
				# violated
				color = (0, 0, 255)
				cv2.rectangle(frame, box[0], box[2], color, 2)
				text = "violated: "
				cv2.putText(frame, text, (box[3][0], box[3][1] + 15),
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

# load our YOLO object detector trained on COCO dataset (80 classes)
# and determine only the *output* layer names that we need from YOLO
print("[INFO] loading YOLO from disk...")
net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)

# Using GPU if flag is passed
if USE_GPU:
	net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
	net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# initialize the video stream, pointer to output video file, and
# frame dimensions
videoStream = cv2.VideoCapture(inputVideoPath)
video_width = int(videoStream.get(cv2.CAP_PROP_FRAME_WIDTH))
video_height = int(videoStream.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Specifying coordinates for a default line 
x1_line = 0
y1_line = video_height//2
x2_line = video_width
y2_line = video_height//2

# Initialization
previous_frame_detections = [{(0,0):0} for i in range(FRAMES_BEFORE_CURRENT)]
# previous_frame_detections = [spatial.KDTree([(0,0)])]*FRAMES_BEFORE_CURRENT # Initializing all trees
num_frames, vehicle_count = 0, 0
tot_num_frame = 0
writer = initializeVideoWriter(video_width, video_height, videoStream)
start_time = int(time.time())

# for testing skipping frames
videoStream.set(cv2.CAP_PROP_POS_FRAMES, 30*73) 
tot_num_frame = 30*73

# loop over frames from the video file stream
while True:
	tot_num_frame += 1
	print ("tot_frame: ", tot_num_frame)
	# print("================NEW FRAME================")
	num_frames+= 1
	# print("FRAME:\t", num_frames)
	# Initialization for each iteration
	boxes, confidences, classIDs = [], [], [] 
	vehicle_crossed_line_flag = False 

	# Calculating fps each second
	start_time, num_frames = displayFPS(start_time, num_frames)
	# read the next frame from the file
	(grabbed, frame) = videoStream.read()

	# if the frame was not grabbed, then we have reached the end of the stream
	if not grabbed:
		break

	# construct a blob from the input frame and then perform a forward
	# pass of the YOLO object detector, giving us our bounding boxes
	# and associated probabilities
	blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (inputWidth, inputHeight),
		swapRB=True, crop=False)
	net.setInput(blob)
	start = time.time()
	layerOutputs = net.forward(ln)
	end = time.time()
	
	# camera position
	pos, angle = pos_angle(tot_num_frame)
	print ("pos, angle:", pos, angle)

	# detection
	# loop over each of the layer outputs
	for output in layerOutputs:
		# loop over each of the detections
		for i, detection in enumerate(output):
			# extract the class ID and confidence (i.e., probability)
			# of the current object detection
			scores = detection[5:]
			classID = np.argmax(scores)
			confidence = scores[classID]

			# filter out weak predictions by ensuring the detected
			# probability is greater than the minimum probability
			if confidence > preDefinedConfidence:
				# scale the bounding box coordinates back relative to
				# the size of the image, keeping in mind that YOLO
				# actually returns the center (x, y)-coordinates of
				# the bounding box followed by the boxes' width and
				# height
				box = detection[0:4] * np.array([video_width, video_height, video_width, video_height])
				(centerX, centerY, width, height) = box.astype("int")

				# use the center (x, y)-coordinates to derive the top
				# and and left corner of the bounding box
				x = int(centerX - (width / 2))
				y = int(centerY - (height / 2))
							
				# Printing the info of the detection
				# print('\nName:\t', LABELS[classID],
					# '\t|\tBOX:\t', x,y)

				# update our list of bounding box coordinates,
				# confidences, and class IDs
				boxes.append([x, y, int(width), int(height)])
				confidences.append(float(confidence))
				classIDs.append(classID)

	# # Changing line color to green if a vehicle in the frame has crossed the line 
	# if vehicle_crossed_line_flag:
	# 	cv2.line(frame, (x1_line, y1_line), (x2_line, y2_line), (0, 0xFF, 0), 2)
	# # Changing line color to red if a vehicle in the frame has not crossed the line 
	# else:
	# 	cv2.line(frame, (x1_line, y1_line), (x2_line, y2_line), (0, 0, 0xFF), 2)

	# apply non-maxima suppression to suppress weak, overlapping
	# bounding boxes
	idxs = cv2.dnn.NMSBoxes(boxes, confidences, preDefinedConfidence,
		preDefinedThreshold)

	# Draw detection box 
	box_car = markDetectionBoxes(idxs, boxes, classIDs, confidences, frame, pos, angle)
	
	# draw parking lot boxes
	box_lots = draw_lot(frame, pos,angle)

	drawViolationBoxes(box_car, box_lots)
	
	# vehicle_count, current_detections = count_vehicles(idxs, boxes, classIDs, vehicle_count, previous_frame_detections, frame)

	# write the output frame to disk
	writer.write(frame)

	cv2.imshow('Frame', frame)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break	
	
	# Updating with the current frame detections
	# previous_frame_detections.pop(0) #Removing the first frame from the list
	# # previous_frame_detections.append(spatial.KDTree(current_detections))
	# previous_frame_detections.append(current_detections)

# release the file pointers
print("[INFO] cleaning up...")
writer.release()
videoStream.release()
