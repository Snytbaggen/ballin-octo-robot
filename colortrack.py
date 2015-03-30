# Raspbery Pi Color Tracking and Robot Steering
# Code by Daniel Haggmyr, with borrowed code from Oscar Liang

import math, pygame
import robot_comm as comm #,serial
import numpy as np
import RPi as GPIO
import cv2.cv as cv
from pygame.locals import *

global frame, rgbj,LOW_TRESHOLD, HIGH_TRESHOLD, hsv_range, comm, serial, hsvi, previous_turn, size_error_preivous, size_error_integral, previous_turn, Kp, Kd, Ki

#Serial port setup
comm.SetSerialPort('/dev/ttyUSB0',9600)

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
manual_control = True
arrow_keys = [False, False, False, False] #Up Down Left Right

#Text constants and font creation
hscale = vscale = 0.4
shear = 0
thickness = 1
line_type = 8
font = cv.InitFont(cv.CV_FONT_HERSHEY_SIMPLEX, hscale, vscale, shear, thickness, line_type)
text_x_offset=5
text_y_offset=15
text_color=(128,255,255)

pygame.init()
screen = pygame.display.set_mode((160,120))
pygame.display.set_caption ('Data window')
background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill((0,0,0))

pygamefont = pygame.font.Font(None, 20)
screen.blit(background, (0,0))
pygame.display.flip()


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

def CalculateMove(radius):
    global size_error_previous, size_error_integral, Kp, Kd, Ki
    
    target_size = 250
    cutoff = 40

    size_error_current = target_size - radius
    size_error_derivative = size_error_current-size_error_previous
    size_error_integral += size_error_current

    move_value = int(Kp * size_error_current + Kd * size_error_derivative + Ki * size_error_integral)
    
    if move_value > cutoff:
        move_value = 255
    elif move_value < -cutoff:
        move_value = -255
    else:
        move_value = 0

    size_error_previous = size_error_current
    return move_value
    

def CalculateTurn(pos):
    global previous_turn
    Kp=-7
    Kd=1
    margin = 5
    target = 160/2 #width/2
    cutoff = 50
    current_turn = target - pos
    turn_value = Kp*(current_turn) + Kd*(current_turn-previous_turn)
    
    if turn_value > cutoff:
        turn_value = 255
    elif turn_value < -cutoff:
        turn_value = -255
    else:
        turn_value = 0

    previous_turn = current_turn
    return turn_value

def CalculateMovement(posX, posY, radius):
    move = CalculateMove(radius)
    turn = CalculateTurn(posX)
    if move < 0:
        turn = -turn
    comm.SendMoveCommand(move, turn)

def exit_program():
    global comm
    comm.SendMoveCommand(0,0)
    comm.Disconnect()
    quit()
    

##########################
#Main program starts here#
##########################

size_error_previous = size_error_integral = 0
previous_turn = 0
Kp = 1
Kd = 10
Ki = 0.0


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
   # pygame.event.pump()
#    keys = pygame.key.get_pressed()
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                if manual_control:
                    arrow_keys[0] = True
                else:
                    hsv_range+=1
                    UpdateTreshold()
            if event.key == pygame.K_DOWN:
                if manual_control:
                    arrow_keys[1] = True
                else:
                    hsv_range-=1
                    UpdateTreshold()
            if event.key == pygame.K_LEFT:
                if manual_control:
                    arrow_keys[2] = True
                else:
                    blob_sensitivity += 250
            if event.key == pygame.K_RIGHT:
                if manual_control:
                    arrow_keys[3] = True
                else:
                    blob_sensitivity -= 250

            if event.key == pygame.K_t:
                hsv_tracking = not hsv_tracking
            if event.key == pygame.K_v:
                video_feed = not video_feed
            if event.key == pygame.K_m:
                manual_control = not manual_control
            if event.key == pygame.K_q:
                exit_program()

            if event.key == pygame.K_KP7:
                Kp += 1
            if event.key == pygame.K_KP4:
                Kp -= 1
            if event.key == pygame.K_KP8:
                Ki += 0.1
            if event.key == pygame.K_KP5:
                Ki -= 0.1
            if event.key == pygame.K_KP9:
                Kd += 1
            if event.key == pygame.K_KP6:
                Kd -= 1

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                if manual_control:
                    arrow_keys[0] = False
            if event.key == pygame.K_DOWN:
                if manual_control:
                    arrow_keys[1] = False
            if event.key == pygame.K_LEFT:
                if manual_control:
                    arrow_keys[2] = False
            if event.key == pygame.K_RIGHT:
                if manual_control:
                    arrow_keys[3] = False

    background.fill((0,0,0))
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
        if not manual_control:
            CalculateMovement(posX, posY, radius)

        #If a blob has been found then also write its position in text on the processed image.
        background.blit(pygamefont.render("blob x, y, r: "+str(posX)+", "+str(posY)+", "+str(radius), 1, (255,255,255)),(text_x_offset,text_y_offset))
    else:
        #If a blob haven't been found then indicate that by writing "N/A" instead of position data.
        background.blit(pygamefont.render("blob x, y: N/A", 1, (255,255,255)),(text_x_offset,text_y_offset))
        comm.SendMoveCommand(0,0)

        size_error_previous = size_error_integral = 0 #Also reset the regulation variables to avoid junk data later

    #Write the rest of the information
    background.blit(pygamefont.render("hsv-range: "+str(hsv_range), 1, (255,255,255)),(text_x_offset,text_y_offset*2))
    background.blit(pygamefont.render("sensitivity: "+str(-1*blob_sensitivity/250), 1, (255,255,255)),(text_x_offset,text_y_offset*3))

    if hsv_tracking:
        background.blit(pygamefont.render("hue Tracking: on", 1, (255,255,255)),(text_x_offset,text_y_offset*4))
    else:
        background.blit(pygamefont.render("hue Tracking: off", 1, (255,255,255)),(text_x_offset,text_y_offset*4))

    if video_feed:
        background.blit(pygamefont.render("Video: on", 1, (255,255,255)),(text_x_offset,text_y_offset*5))    
    else:
        background.blit(pygamefont.render("Video: off", 1, (255,255,255)),(text_x_offset,text_y_offset*5))
    
    if manual_control:
        background.blit(pygamefont.render("Manual control: on", 1, (255,255,255)),(text_x_offset,text_y_offset*6))        
    else:
        background.blit(pygamefont.render("Manual control: off", 1, (255,255,255)),(text_x_offset,text_y_offset*6))  

    #background.blit(pygamefont.render("PID: "+str(Kp) + ", " + str(Ki) + ", " + str(Kd), 1, (255,255,255)), (text_x_offset, text_y_offset*7))

    screen.blit(background, (0,0))
    pygame.display.flip()

    if manual_control:
        keys = pygame.key.get_pressed()
        turn = move = 0
        if arrow_keys[0]: #up
            move = 255
        elif arrow_keys[1]: #down
            move = -255
        if arrow_keys[2]: #left
            turn = -255
        elif arrow_keys[3]: #right
            turn = 255
        comm.SendMoveCommand(move, turn)

    #Show the processed and original image.
    cv.ShowImage("Processed", imgColorProcessed)
    if video_feed:
        cv.ShowImage("Original", frame)
    else:
        cv.ShowImage("Original", blank_image)

    #arrow_keys = [False, False, False, False]
    
    #Wait for key press, and if a key has been pressed then act accordingly.
    #This function call is very important because it also handles a lot of stuff
    #regarding the windows.
    pygame.event.pump()
    key = cv.WaitKey(1)
