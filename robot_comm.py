import serial

global serial_comm
previous_move = previous_turn = 0

def SetSerialPort(port, baudrate):
    global serial_comm
    serial_comm = serial.Serial(port, baudrate)
    serial_comm.open()

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

def BuildExtraCommand(val1, val2):
    cmd = "E"
    val1 = FormatExtraCommandValue(val1)
    val2 = FormatExtraCommandValue(val2)
    cmd += IntToStr(val1) + IntToStr(val2)
    
    
def SendCommand(cmd):
    global serial_comm
    serial_comm.write(cmd)
    answer = serial_comm.read()
    if answer == 'K':
        #everything OK, return
        return
    elif answer == 'F':
        #Fault command sent, notify user
        print "Faulty command sent: " + cmd
    else:
        #This should never happen
        print "ERROR: Unknown answer from robot (" + answer + ") when sending command " + cmd

def SendMoveCommand(move, turn):
    global previous_move, previous_turn
    
    #Only send if the new values differs from the last ones, resending the same value will
    #do nothing since the robot is already moving/turning in that direction with that speed
    if move != previous_move:
        SendCommand(BuildMoveCommand(move).encode('utf-8'))
    if turn != previous_turn:
        SendCommand(BuildTurnCommand(turn).encode('utf-8'))
    previous_move = move
    previous_turn = turn

def SendExtraCommand(val1, val2):
    SendCommand(BuildExtraCommand(val1, val2).encode('utf-8'))

def HeadlightsOn():
    SendCommand("H111100".encode('utf-8'))

def HeadlightsOff():
    SendCommand("H000000".encode('utf-8'))

def Disconnect():
    global serial_comm
    serial_comm.close()
