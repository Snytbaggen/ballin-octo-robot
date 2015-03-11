#define engine_black 3
#define engine_red 5
#define steering_red 6
#define steering_black 9
#define laser_x 10
#define laser_y 11
#define laser 4
#define left_led 7
#define right_led 8

int engine_motor[2], steering_motor[2], laser_servos[2];

void setup(){
  engine_motor[0] = engine_red;
  engine_motor[1] = engine_black;
  
  steering_motor[0] = steering_red;
  steering_motor[1] = steering_black;
  
  laser_servos[0] = laser_x;
  laser_servos[1] = laser_y;
  
  pinMode(engine_motor[0], OUTPUT);
  pinMode(engine_motor[1], OUTPUT);
  pinMode(steering_motor[0], OUTPUT);
  pinMode(steering_motor[1], OUTPUT);
  pinMode(laser_servos[0], OUTPUT);
  pinMode(laser_servos[1], OUTPUT);
  
  Serial.begin(9600);
}

void loop(){
}

void serialEvent(){
  String cmd = "";
  while (cmd.length() < 7){
    if (Serial.available()){
      cmd += (char)Serial.read();
    }
  }
  if (isValidCommand(cmd)){
    executeCommand(cmd);
  }
}

boolean isValidCommand(String cmd){
  if (cmd.length() == 7){
    char cmd_type = cmd[0];
    switch (cmd_type){
      case 'F': //Forward
      case 'B': //Backward
      case 'L': //Left
      case 'R': //Right
      case 'S': //Stop
      case 'E': //Extra (for non-movement stuff)
        break;  //command type OK, move on to check arguments
      default:
        return false;
    }
    int cmd_arg1 = cmd.substring(1,4).toInt();
    int cmd_arg2 = cmd.substring(4).toInt();
    if (cmd_arg1 <= 255 && cmd_arg2 <= 255){
      Serial.println("K"); //Arguments looks OK, sent ack
      return true;
    }
  }
  Serial.println("F"); //Something wrong, notify sender
  return false;
}

void executeCommand(String cmd){
  char cmd_type = cmd[0];
  int cmd_arg1 = cmd.substring(1,4).toInt();
  int cmd_arg2 = cmd.substring(4).toInt();
  switch (cmd_type){
      case 'F': //Forward
        set_motor_value(engine_motor, 0, cmd_arg1);
        break;
      case 'B': //Backward
        set_motor_value(engine_motor, cmd_arg1, 0);
        break;
      case 'L': //Left
        set_motor_value(steering_motor, 0, cmd_arg1);
        break;
      case 'R': //Right
        set_motor_value(steering_motor, cmd_arg1, 0);
        break;
      case 'S': //Stop
        set_motor_value(steering_motor, 0, 0);
        set_motor_value(engine_motor, 0, 0);
        break;
      case 'E': //Extra (for non-movement stuff)
        set_motor_value(laser_servos, cmd_arg1, cmd_arg2);
        break;  //command type OK, move on to check arguments
      default:
        return; //This shouldn't happen
  }
}

void set_motor_value(int motor[], int val1, int val2){
  analogWrite(motor[0], val1);
  analogWrite(motor[1], val2);
}
