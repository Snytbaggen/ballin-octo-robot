import serial

global serial_comm

def SetSerialPort(port, baudrate):
    global serial_comm
    serial_comm = serial.Serial(port, baudrate)

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
 #   answer = serial.read()
    answer = 'K'
    if answer == 'K':
        return
    elif answer == 'F':
        print("Faulty command, sending again\n")
    else:
        print("Unknown error, sending again\n")

def SendMoveCommand(speed, turn):
    SendCommand(BuildSpeedCommand(speed).encode('utf-8'))
    SendCommand(BuildTurnCommand(turn).encode('utf-8'))

def SendExtraCommand(val1, val2):
    SendCommand(BuildExtraCommand(val1, val2).encode('utf-8'))
