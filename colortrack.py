# Raspbery Pi Color Tracking Project
# Code written by Oscar Liang
# 30 Jun 2013

import math
import numpy as np
import RPi as GPIO
import cv2.cv as cv

global frame, rgbj,LOW_TRESHOLD, HIGH_TRESHOLD, hsv_range

# captured image size
width = 160
height = 120

#Inital treshold and range values choosen by experimentation
LOW_TRESHOLD = 74,84,90
HIGH_TRESHOLD = 143,171,255
hsv_range=50
blob_sensitivity=0

#Booleans
hsv_recalculate = False
data_on = False
window_exists = False

#Text constants and font creation
hscale = vscale = 0.4
shear = 0
thickness = 1
line_type = 8
font = cv.InitFont(cv.CV_FONT_HERSHEY_SIMPLEX, hscale, vscale, shear, thickness, line_type)
text_x_offset=5
text_y_offset=15
text_color=(128,255,255)


def MyMouseCallback(event, x, y, flags, param):
    global rgbj,LOW_TRESHOLD,HIGH_TRESHOLD, hsv_range
    if event==cv.CV_EVENT_LBUTTONDBLCLK:		# Here event is left mouse button double-clicked
        hsv=cv.CreateImage(cv.GetSize(frame),8,3)
        cv.CvtColor(frame,hsv,cv.CV_BGR2HSV)
        rgbj = cv.Get2D(hsv, y, x)
        UpdateTreshold()

def ColorProcess(img):
    # returns thresholded image
    imgHSV = cv.CreateImage(cv.GetSize(img), 8, 3)

    # converts BGR image to HSV
    cv.CvtColor(img, imgHSV, cv.CV_BGR2HSV)
    imgProcessed = cv.CreateImage(cv.GetSize(img), 8, 1)

    # converts the pixel values lying within the range to 255 and stores it in the destination
    cv.InRangeS(imgHSV, LOW_TRESHOLD, HIGH_TRESHOLD, imgProcessed)
    return imgProcessed

def UpdateTreshold():
    global LOW_TRESHOLD, HIGH_TRESHOLD, hsv_range
    LOW_TRESHOLD = [rgbj[0]-hsv_range, rgbj[1]-hsv_range,rgbj[2]-hsv_range]
    HIGH_TRESHOLD = [rgbj[0]+hsv_range, rgbj[1]+hsv_range,rgbj[2]+hsv_range]


##########################
#MAIN PROGRAM STARTS HERE#
##########################
capture = cv.CreateCameraCapture(0)

# Over-write default captured image size
cv.SetCaptureProperty(capture,cv.CV_CAP_PROP_FRAME_WIDTH,width)
cv.SetCaptureProperty(capture,cv.CV_CAP_PROP_FRAME_HEIGHT,height)

#Create windows
cv.NamedWindow( "Original", 1 )
cv.NamedWindow( "Processed", 1 )

#Set mouse callback to the unprocessed window
cv.SetMouseCallback("Original",MyMouseCallback)

#Main loop. Code for fetching and processing the image has been copied and slightly modified from code
#written by Oscar Liang that was uploaded online
while True:
    #Fetch frame and blur it. Copied code starts here.
    frame = cv.QueryFrame(capture)
    cv.Smooth(frame, frame, cv.CV_BLUR, 3)

    imgColorProcessed = ColorProcess(frame)
    mat = cv.GetMat(imgColorProcessed)

    # Calculate the moments
    moments = cv.Moments(mat, 0)
    area = cv.GetCentralMoment(moments, 0, 0)
    moment10 = cv.GetSpatialMoment(moments, 1, 0)
    moment01 = cv.GetSpatialMoment(moments, 0,1)

    # Find a big enough blob
    #The area condition has been modified to account for user-chosen
    #sensitivity. The area value has also been adjusted for the different
    #camera resolution used in this project.
    if(area > 15000+blob_sensitivity):

        # Calculating the center postition of the blob
        posX = int(moment10 / area)
        posY = int(moment01 / area)

        #update HSV value from middle of blob
        if hsv_recalculate:
            hsv=cv.CreateImage(cv.GetSize(frame),8,3)
            cv.CvtColor(frame,hsv,cv.CV_BGR2HSV)
            rgbj = cv.Get2D(hsv, posY, posX)
            LOW_TRESHOLD = [rgbj[0]-hsv_range, rgbj[1]-hsv_range,rgbj[2]-hsv_range]
            HIGH_TRESHOLD = [rgbj[0]+hsv_range, rgbj[1]+hsv_range,rgbj[2]+hsv_range]

        radius = int(math.sqrt(area/math.pi))
#        data_image = cv.CreateImage((160,120),8,3)
        cv.Circle(frame, (posX, posY), radius/15, (0,0,255), 2,8,0)
        cv.PutText(imgColorProcessed, "Blob X, Y: "+str(posX)+", "+str(posY), (text_x_offset,text_y_offset), font, text_color)
    else:
        cv.PutText(imgColorProcessed, "Blob X, Y: N/A", (text_x_offset,text_y_offset), font, (128,255,255))
    cv.PutText(imgColorProcessed, "HSV-range: "+str(hsv_range), (text_x_offset,text_y_offset*2), font, text_color)
    cv.PutText(imgColorProcessed, "Sensitivity: "+str(-1*blob_sensitivity/250), (text_x_offset,text_y_offset*3), font, text_color)
    if hsv_recalculate:
        cv.PutText(imgColorProcessed, "Hue tracking: On", (text_x_offset,text_y_offset*4), font, text_color)
    else:
        cv.PutText(imgColorProcessed, "Hue tracking: Off", (text_x_offset,text_y_offset*4), font, text_color)
        
    cv.ShowImage("Processed", imgColorProcessed)
    cv.ShowImage("Original", frame)
    if data_on:
        if not window_exists:
            cv.NamedWindow("data",1)
            window_exists = True
        cv.ShowImage("data", data_image)
    else:
        if window_exists:
            cv.DestroyWindow("data")
            window_exists = False
            
    
    #TODO: print when parameters changes
    key = cv.WaitKey(10)
    #if key > 0:
    #    print key
    if key == 1048676: #d, toggle data
        data_on = not data_on
    if key == 1048689: #q, quit
        break
    if key == 1048692: #t, toggle hue tracking
        hsv_recalculate = not hsv_recalculate
    if key == 1113938: #up arrow, increase hsv range
        hsv_range+=1
        UpdateTreshold()
    if key == 1113940: #down arrow, decrease hsv range
        hsv_range-=1
        UpdateTreshold(hsv_range)
    if key == 1113937: #left arrow, increase detection sensitivity (detects smaller blobs)
        blob_sensitivity += 250
    if key == 1113939: #right arrow, decrease detection sensitivity (ignores smaller blobs)
        blob_sensitivity -= 250
    #    break
    #    a=1
