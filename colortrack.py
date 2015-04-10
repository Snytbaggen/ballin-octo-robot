# Raspbery Pi Color Tracking and Robot Steering
# Code by Daniel Haggmyr, with borrowed code from Oscar Liang

import math, pygame, time
import robot_comm as comm #,serial
import numpy as np
import RPi as GPIO
import cv2.cv as cv
from pygame.locals import *

#Serial port setup
comm.SetSerialPort('/dev/ttyUSB0',19200)
time.sleep(2) #some delay necessary to prevent starting to talk with the arduino too fast

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
headlights_on = False
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

#A pygame window is used to read the keyboard and show information
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
    global LOW_TRESHOLD, HIGH_TRESHOLD
    LOW_TRESHOLD = [hsvi[0]-hsv_range, hsvi[1]-hsv_range,hsvi[2]-hsv_range]
    HIGH_TRESHOLD = [hsvi[0]+hsv_range, hsvi[1]+hsv_range,hsvi[2]+hsv_range]

# Calculates if the robot should move forward or backwards depending on ball size.
# A simple PD controller is used with values chosen from experimentation. Only full stop
# and full speed is used because of weak motors. The protocol supports PWM.
def CalculateMove(radius):
    global size_error_previous
    Kp = 1  #Proportional constant
    Kd = 10 #Derivative constant
    
    target_size = 250 #Target radius for the ball, chosen by experiment
    cutoff = 40 #Cutoff to counter "jitter" in the size caused by camera, chosen by experiment 

    size_error_current = target_size - radius
    size_error_derivative = size_error_current-size_error_previous

    move_value = Kp * size_error_current + Kd * size_error_derivative
    
    if move_value > cutoff:
        move_value = 255
    elif move_value < -cutoff:
        move_value = -255
    else:
        move_value = 0

    size_error_previous = size_error_current
    return move_value
    
# Calculates if the robot should move left or right depending on ball position.
# A simple PD controller is used with values chosen from experimentation. Only full stop
# and full speed is used because of weak motors. The protocol supports PWM.. 
def CalculateTurn(current_position):
    global position_error_previous
    Kp = -4 #Proportional constant
    Kd = -2 #Derivative constant

    target_position = width/2
    cutoff = 50 # Cutoff to counter "jitter" in the position caused by camera, chosen by experiment

    position_error_current = target_position - current_position
    position_error_derivative = position_error_current - position_error_previous

    turn_value = Kp * position_error_current + Kd * position_error_derivative

    if turn_value > cutoff:
        turn_value = 255
    elif turn_value < -cutoff:
        turn_value = -255
    else:
        turn_value = 0

    position_error_previous = position_error_current
    return turn_value

def CalculateMovement(posX, posY, radius):
    move = CalculateMove(radius)
    turn = CalculateTurn(posX)
    if move < 0:
        turn = -turn

    # If the ball is too close the camera might cut it off making it appear to be far away
    # because of a smaller area. To prevent this the robot doesn't move if the Y position is above
    # a certain treshold (Y=0 at top of the image)
    if posY > 85:
        move = 0
    comm.SendMoveCommand(move, turn)

def exit_program():
    comm.SendMoveCommand(0,0)
    comm.HeadlightsOff()
    comm.Disconnect()
    quit()
    

##########################
#Main program starts here#
##########################

size_error_previous = 0
position_error_previous = 0
previous_turn = 0

capture = cv.CreateCameraCapture(0)

# Over-write default captured image size
cv.SetCaptureProperty(capture,cv.CV_CAP_PROP_FRAME_WIDTH,width)
cv.SetCaptureProperty(capture,cv.CV_CAP_PROP_FRAME_HEIGHT,height)

#Create windows
cv.NamedWindow( "Original", 1 )
cv.NamedWindow( "Processed", 1 )

#Set mouse callback to the unprocessed window
cv.SetMouseCallback("Original",MyMouseCallback)

comm.HeadlightsOn()
headlights_on = True

#Main loop. Code for fetching and processing the image has been copied and slightly modified from code
#written by Oscar Liang that was uploaded online
while True:
    #Read keyboard buttons
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.KEYDOWN: #Key press is detected
            #Read directional buttons, increase sensitivity/range or
            #set move/turn directions depending on manual control is off or on
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

            #Read other relevant keys
            if event.key == pygame.K_t: #Toggle tracking
                hsv_tracking = not hsv_tracking
            if event.key == pygame.K_v: #Toggle video feed
                video_feed = not video_feed
            if event.key == pygame.K_m: #Toggle manual control
                manual_control = not manual_control
            if event.key == pygame.K_h: #Toggle headlights
                if (headlights_on):
                    comm.HeadlightsOff()
                else:
                    comm.HeadlightsOn()
                headlights_on = not headlights_on
            if event.key == pygame.K_q: #Quit
                exit_program()

        if event.type == pygame.KEYUP: #Key release is detected
            #Read directional arrows, disable turn/move directions
            #for pressed buttons.
            if event.key == pygame.K_UP:
                arrow_keys[0] = False
            if event.key == pygame.K_DOWN:
                arrow_keys[1] = False
            if event.key == pygame.K_LEFT:
                arrow_keys[2] = False
            if event.key == pygame.K_RIGHT:
                arrow_keys[3] = False

    background.fill((0,0,0))
    #Fetch frame and blur it. 
    #Copied code starts here:
    frame = cv.QueryFrame(capture)
    cv.Smooth(frame, frame, cv.CV_BLUR, 3)

    imgColorProcessed = ColorProcess(frame)
    mat = cv.GetMat(imgColorProcessed)

    # Calculate the moments
    moments = cv.Moments(mat, 0)
    area = cv.GetCentralMoment(moments, 0, 0)
    moment10 = cv.GetSpatialMoment(moments, 1, 0)
    moment01 = cv.GetSpatialMoment(moments, 0,1)

    # Find a big enough blob. The area condition has been modified to account for
    # user-chosen sensitivity and the different camera resolution used in this code
    if(area > 15000+blob_sensitivity):

        # Calculating the center postition of the blob
        posX = int(moment10 / area)
        posY = int(moment01 / area) 
        #Copied code ends here

        # Update HSV value from middle of blob.
        # Inaccurate, an average value would be a lot better
        if hsv_tracking:
            ReadHsvValue(frame,posX,posY)
        
        # Calculate a value from the area proportional to the object's radius, assuming
        # it is a circle. Then draw a circle for visual aid around the object, with the
        # divisor 15 choosen by experiment to be "good enough".
        radius = int(math.sqrt(area/math.pi))
        cv.Circle(frame, (posX, posY), radius/15, (0,0,255), 2,8,0)

        if not manual_control:
            CalculateMovement(posX, posY, radius) #Calculates move and turn values

        #If a blob has been found, write its position in text on the processed image.
        background.blit(pygamefont.render("blob x, y, r: "+str(posX)+", "+str(posY)+", "+str(radius), 1, (255,255,255)),(text_x_offset,text_y_offset-10))
    else:
        #If a blob haven't been found, indicate that by writing "N/A" instead of position data.
        background.blit(pygamefont.render("blob x, y: N/A", 1, (255,255,255)),(text_x_offset,text_y_offset-10))
        comm.SendMoveCommand(0,0)

        size_error_previous = size_error_integral = 0 #Also reset the regulation variables to avoid junk data later

    #Write other information on screen
    background.blit(pygamefont.render("hsv-range: "+str(hsv_range), 1, (255,255,255)),(text_x_offset,text_y_offset*2-10))
    background.blit(pygamefont.render("sensitivity: "+str(-1*blob_sensitivity/250), 1, (255,255,255)),(text_x_offset,text_y_offset*3-10))

    if hsv_tracking:
        background.blit(pygamefont.render("hue Tracking: on", 1, (255,255,255)),(text_x_offset,text_y_offset*4-10))
    else:
        background.blit(pygamefont.render("hue Tracking: off", 1, (255,255,255)),(text_x_offset,text_y_offset*4-10))

    if video_feed:
        background.blit(pygamefont.render("Video: on", 1, (255,255,255)),(text_x_offset,text_y_offset*5-10))    
    else:
        background.blit(pygamefont.render("Video: off", 1, (255,255,255)),(text_x_offset,text_y_offset*5-10))
    
    if manual_control:
        background.blit(pygamefont.render("Manual control: on", 1, (255,255,255)),(text_x_offset,text_y_offset*6-10))        
    else:
        background.blit(pygamefont.render("Manual control: off", 1, (255,255,255)),(text_x_offset,text_y_offset*6-10))  
    if headlights_on:
        background.blit(pygamefont.render("Headlights: on", 1, (255,255,255)), (text_x_offset, text_y_offset*7-10))
    else:
        background.blit(pygamefont.render("Headlights: off", 1, (255,255,255)), (text_x_offset, text_y_offset*7-10))
    screen.blit(background, (0,0))
    pygame.display.flip()
    
    #Set turn values if manual control is enabled
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
    
    pygame.event.pump()  #Load key events
    key = cv.WaitKey(10) #Handles important things, among other things images will not show if this isn't called.
