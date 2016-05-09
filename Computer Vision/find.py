import cv2
import numpy as np
from matplotlib import pyplot as plt
import time

def what_to_find():
    webcam = cv2.VideoCapture(0)
    print('Cheese!!')
    time.sleep(3)
    value, image = webcam.read()
    #cv2.imshow('what to find?',webcam)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    cv2.imwrite('find.png', image_rgb)
    print("Ok!")   
    webcam.release()

print("what should I look for?")
print("Put the object you what to be found in front of your Webcam")
time.sleep(2)
print('3')
time.sleep(1)
print('2')
time.sleep(1)
print('1')
what_to_find()
#print('starting search ...')
#execfile('homography_videoplay.py')


