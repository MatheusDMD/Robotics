import cv2
import numpy as np
from matplotlib import pyplot as plt
import time

#Before using this run find.py to generate the image this program is going to search for.


#cap = cv2.VideoCapture('hall_box_battery.mp4')
cap = cv2.VideoCapture(0)


while(True):
	# Capture frame-by-frame
	ret, frame = cap.read()

    
	# Our operations on the frame come here
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


	MIN_MATCH_COUNT = 10
	try:
		img1 = cv2.imread('find.png',0)          # Imagem a procurar

		img2 = frame # Imagem do cenario - puxe do video para fazer isto

		# Initiate SIFT detector
		sift = cv2.SIFT()

		# find the keypoints and descriptors with SIFT in each image
		kp1, des1 = sift.detectAndCompute(img1,None)
		kp2, des2 = sift.detectAndCompute(img2,None)

		FLANN_INDEX_KDTREE = 0
		index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
		search_params = dict(checks = 50)

		# Configura o algoritmo de casamento de features
		flann = cv2.FlannBasedMatcher(index_params, search_params)

		# Tenta fazer a melhor comparacao usando o algoritmo
		matches = flann.knnMatch(des1,des2,k=2)

		# store all the good matches as per Lowe's ratio test.
		good = []
		for m,n in matches:
		    if m.distance < 0.7*n.distance:
		        good.append(m)


		if len(good)>MIN_MATCH_COUNT:
		    # Separa os bons matches na origem e no destino
		    src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
		    dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)


		    # Tenta achar uma trasformacao composta de rotacao, translacao e escala que situe uma imagem na outra
		    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
		    matchesMask = mask.ravel().tolist()

		    h,w = img1.shape
		    pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)

		    # Transforma os pontos da imagem origem para onde estao na imagem destino2
		    dst = cv2.perspectiveTransform(pts,M)

		    # Desenha as linhas
		    img2b = cv2.polylines(img2,[np.int32(dst)],True,255,3, cv2.CV_AA)

		else:
		    print "Not enough matches are found - %d/%d" % (len(good),MIN_MATCH_COUNT)
		    matchesMask = None

		#draw_params = dict(matchColor = (0,255,0), # draw matches in green color
		#                   singlePointColor = None,
		#                   matchesMask = matchesMask, # draw only inliers
		#                   flags = 2)

		#img3 = drawMatches(img1,kp1,img2,kp2,good[:20])

		# Display the resulting frame
		cv2.imshow('frame',frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
		    break
	except:
		print("You don't have a file to be found, \nmaybe you forgot to run find.py")
		break
# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()