# Raspbery Pi Color Tracking and Robot Steering
# Code by Daniel Haggmyr, with borrowed code from Oscar Liang

import math, serial
import numpy as np
import RPi as GPIO
import cv2.cv as cv

global frame, rgbj,LOW_TRESHOLD, HIGH_TRESHOLD, hsv_range, serial

#Serial port setup
serial = serial.Serial('/dev/ttyUSB0',9600)

# captured image size
width = 160
height = 120
blank_image = cv.CreateImage((width,height),8,3) 

#Inital treshold and range values choosen by experimentation
LOW_TRESHOLD = 74,84,90
HIGH_TRESHOLD = 143,171,255
hsv_range=50
blob_sensitivity=0

#Booleans
hsv_tracking = False
data_on = False
window_exists = False
video_feed = True

#Text constants and font creation
hscale = vscale = 0.4
shear = 0
thickness = 1
line_type = 8
font = cv.InitFont(cv.CV_FONT_HERSHEY_SIMPLEX, hscale, vscale, shear, thickness, line_type)
text_x_offset=5
text_y_offset=15
text_color=(128,255,255)

def IntToStr(number):
    ret = ""
    if number < 100:
        ret+= "0"
        if number < 10:
            ret +="0"
    ret += str(number)
    return ret

def BuildSpeedCommand(speed):
    cmd = ""
    if speed >= 0:
        cmd = "F"
    else:
        cmd = "B"
        speed = -speed
    if speed > 255:
        speed = 255
    cmd+=IntToStr(speed)+"000"
    return cmd

def BuildTurnCommand(turn):
    cmd = ""
    if turn >= 0:
        cmd = "L"
    else:
        cmd = "R"
        turn = -turn
    if turn > 255:
        turn = 255
    cmd += IntToStr(turn)+"000"
    return cmd

def SendCommand(speed, turn):
    global serial
    serial.write(BuildSpeedCommand(speed).encode('utf-8'))
    #should wait for OK here
    serial.write(BuildTurnCommand(turn).encode('utf-8'))
    #should wait for OK here

#Reads the HSV value in a certain pixel in a given image.
#This code is modified from the original code Oscar Liang wrote.
def ReadHsvValue(image,x,y):
    global hsvi
    hsv=cv.CreateImage(cv.GetSize(image),8,3)
    cv.CvtColor(image,hsv,cv.CV_BGR2HSV)
    hsvi = cv.Get2D(hsv, y, x)
    UpdateTreshold()

#Is called on mouse events.
def MyMouseCallback(event, x, y, flags, param):
    global frame
    if event==cv.CV_EVENT_LBUTTONDBLCLK:
        ReadHsvValue(frame,x,y)

#This turns a BGR color image into an HSV image, as well as
#filters colors depending on a lower and upper treshold. The image is
#returned as a black and white image, where white is the filtered out
#color. Code and comments copied from the original code by Oscar Liang.
def ColorProcess(img):
    # returns thresholded image
    imgHSV = cv.CreateImage(cv.GetSize(img), 8, 3)

    # converts BGR image to HSV
    cv.CvtColor(img, imgHSV, cv.CV_BGR2HSV)
    imgProcessed = cv.CreateImage(cv.GetSize(img), 8, 1)

    # converts the pixel values lying within the range to 255 and stores it in the destination
    cv.InRangeS(imgHSV, LOW_TRESHOLD, HIGH_TRESHOLD, imgProcessed)
    return imgProcessed

#Updates the tresholds used in the ColorProcess function above, depending on the
#hsv-range variable.
def UpdateTreshold():
    global LOW_TRESHOLD, HIGH_TRESHOLD, hsv_range
    LOW_TRESHOLD = [hsvi[0]-hsv_range, hsvi[1]-hsv_range,hsvi[2]-hsv_range]
    HIGH_TRESHOLD = [hsvi[0]+hsv_range, hsvi[1]+hsv_range,hsvi[2]+hsv_range]

##########################
#Main program starts here#
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
        #Copied code ends here
        

        #Update HSV value from middle of blob.
        #Kind of inaccurate, an average value would be a lot better
        if hsv_tracking:
            ReadHsvValue(frame,posX,posY)
        
        #Calculate a value from the area proportional to the object's radius, assuming
        #it is a circle. Then draw a circle for visual aid around the object, with the
        #divisor 15 choosen by experiment to be "good enough".
        radius = int(math.sqrt(area/math.pi))
        cv.Circle(frame, (posX, posY), radius/15, (0,0,255), 2,8,0)

        #TODO: Put regulation and robot movement here
        turn = (posX-width/2)*3
        SendCommand(turn, 0)

        #If a blob has been found then also write its position in text on the processed image.
        cv.PutText(imgColorProcessed, "Blob X, Y: "+str(posX)+", "+str(posY), (text_x_offset,text_y_offset), font, text_color)
    else:
        #If a blob haven't been found then indicate that by writing "N/A" instead of position data.
        cv.PutText(imgColorProcessed, "Blob X, Y: N/A", (text_x_offset,text_y_offset), font, (128,255,255))

    #Put the rest of the text on the processed image.
    cv.PutText(imgColorProcessed, "HSV-range: "+str(hsv_range), (text_x_offset,text_y_offset*2), font, text_color)
    cv.PutText(imgColorProcessed, "Sensitivity: "+str(-1*blob_sensitivity/250), (text_x_offset,text_y_offset*3), font, text_color)

    if hsv_tracking:
        cv.PutText(imgColorProcessed, "Hue tracking: On", (text_x_offset,text_y_offset*4), font, text_color)
    else:
        cv.PutText(imgColorProcessed, "Hue tracking: Off", (text_x_offset,text_y_offset*4), font, text_color)

    if video_feed:
        cv.PutText(imgColorProcessed, "Video: On", (text_x_offset,text_y_offset*5), font, text_color)        
    else:
        cv.PutText(imgColorProcessed, "Video: Off", (text_x_offset,text_y_offset*5), font, text_color)        
    
    #Show the processed and original image.
    cv.ShowImage("Processed", imgColorProcessed)
    if video_feed:
        cv.ShowImage("Original", frame)
    else:
        cv.ShowImage("Original", blank_image)
    
    #Wait for key press, and if a key has been pressed then act accordingly.
    #This function call is very important because it also handles a lot of stuff
    #regarding the windows.
    key = cv.WaitKey(10)
    #if key > 0:    #Uncomment these lines to output the raw key data,
    #    print key  #useful for when adding more keypresses.
    if key == 1048689: #q, quit
        SendCommand(0,0) #Stop motors
        break
    if key == 1048692: #t, toggle hue tracking
        hsv_tracking = not hsv_tracking
    if key == 1113938: #up arrow, increase hsv range
        hsv_range+=1
        UpdateTreshold()
    if key == 1048694: #v, toggle video feed
        video_feed = not video_feed
    if key == 1113940: #down arrow, decrease hsv range
        hsv_range-=1
        UpdateTreshold()
    if key == 1113937: #left arrow, increase detection sensitivity (detects smaller blobs)
        blob_sensitivity += 250
    if key == 1113939: #right arrow, decrease detection sensitivity (ignores smaller blobs)
        blob_sensitivity -= 250
