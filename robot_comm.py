import serial

#Command length is always 7 characters: 1 letter and 6 numbers. For turn/move only the first three
#are used, and ranges between 0-255. For the headlights the first four are used, one for each light
#where 1 is on and 0 is off.

def SetSerialPort(port, baudrate):
    global serial_comm
    serial_comm = serial.Serial(port, baudrate)
    serial_comm.open()
    #If the port cannot be opened the program will halt with an error message. If the open()
    #call returns the port is assumed to be open and functioning.

def IntToStr(number):
    ret = ""
    if number < 100:
        ret+= "0"
        if number < 10:
            ret +="0"
    ret += str(number)
    return ret

def FormatExtraCommandValue(val):
    if val < 0:
        val = 0
    elif val > 999:
        val = 999
    return val

def BuildMoveCommand(move):
    cmd = ""
    if move >= 0:
        cmd = "F"
    else:
        cmd = "B"
        move = -move
    if move > 255:
        move = 255
    cmd+=IntToStr(move)+"000"
    return cmd

def BuildTurnCommand(turn):
    cmd = ""
    if turn >= 0:
        cmd = "R"
    else:
        cmd = "L"
        turn = -turn
    if turn > 255:
        turn = 255
    cmd += IntToStr(turn)+"000"
    return cmd
    
    
def SendCommand(cmd):
    #Check if port is set up. Since it is defined in SetSerialPort() which will stop
    #the program if it can't open a port, it's assumed that the port will work if the
    #variable exists.
    if not 'serial_comm' in globals():
        print "ERROR: No serial port set"
        return

    serial_comm.write(cmd)

    answer = serial_comm.read()
    if answer == 'K':
        #everything OK, return
        return
    elif answer == 'F':
        #Fault command sent, notify user
        print "Faulty command sent: " + cmd
    else:
        #This should never happen since the arduino can only send K or F
        print "ERROR: Unknown answer from robot (" + answer + ") when sending command " + cmd

def SendMoveCommand(move, turn):
    #Set up global variables on first function call. The check is done so the value initialization
    #to 0 is only done once.
    if not 'previous_move'in globals() and not 'previous_turn' in globals():
        global previous_move, previous_turn
        previous_move = previous_turn = 0
    
    #Only send if the new values differs from the last ones, resending the same value will
    #do nothing since the robot is already moving/turning in that direction with that speed
    if move != previous_move:
        SendCommand(BuildMoveCommand(move).encode('utf-8'))
        previous_move = move
    if turn != previous_turn:
        SendCommand(BuildTurnCommand(turn).encode('utf-8'))
        previous_turn = turn

def HeadlightsOn():
    SendCommand("H111100".encode('utf-8'))

def HeadlightsOff():
    SendCommand("H000000".encode('utf-8'))

def Disconnect():
    #Check if a port exists first. Because of how SetSerialPort() works it's assumed to be
    #open and working.
    if not 'serial_comm' in globals():
        print "ERROR: No serial port set"
        return
    serial_comm.close()
