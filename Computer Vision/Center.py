from __future__ import print_function

import numpy as np
import cv2
import sys
import math


#não funciona efetivamente

cap = cv2.VideoCapture("hall_box_battery.mp4")


while(cap.isOpened()):
	
	s, img = cap.read()
	
	winName = "Movement Indicator"
	
	cv2.namedWindow(winName, cv2.WINDOW_AUTOSIZE)
	
	edges = cv2.Canny(img, 100, 300)
	cdst = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

	if True: 
		
		lines = cv2.HoughLinesP(edges, 1, math.pi/180.0, 40, np.array([]), 80, 50)
		
		a,b,c = lines.shape		
		
		for i in range(a):
			x = 0
			j = 0
			while x==0 :
				if abs(lines[i][j][0] - lines[i][j][2])< 50:
					j+=1
				else :
					cv2.line(cdst, (lines[i][j][0], lines[i][j][1]), (lines[i][j][2], lines[i][j][3]), (0, 0, 255), 3, cv2.CV_AA)
					cv2.line(cdst, (lines[i][j+1][0], lines[i][j+1][1]), (lines[i][j+1][2], lines[i][j+1][3]), (0, 0, 255), 3, cv2.CV_AA)

					deltaXA = abs(lines[i][j][2] - lines[i][j][0])
					deltaXB = abs(lines[i][j+1][2] - lines[i][j+1][0])
					XA = lines[i][j][0]
					XB = lines[i][j+1][2]
					cont = 0
					while XA < XB:
						XA += deltaXA
						XB += deltaXB
						cont+=1
						if cont > 20:
							break


					Y = (((float(lines[i][j][1]) +float(lines[i][j][3]))/2)+((float(lines[i][j+1][1])+float(lines[i][j+1][3]))/2))/2
					Yi = Y - 20
					Yf = Y + 20
					#center
					cv2.line(cdst, (int(XA),int(Yi)),(int(XA),int(Yf)),(255, 0, 0),3,cv2.CV_AA)
					cv2.line(cdst, (int(XB),int(Yi)),(int(XB),int(Yf)),(255, 0, 0),3,cv2.CV_AA)
					cv2.line(cdst, (int(XA),int(Y)),(int(XB),int(Y)),(255, 0, 0),3,cv2.CV_AA)
					x=1




			
    

	cv2.imshow('detected lines', cdst)

	if cv2.waitKey(50) & 0xff == ord('q'):
		break

cam.release()
cv2.destroyAllWindows()