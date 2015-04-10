#define engine_black 9
#define engine_red 6
#define steering_yellow 5
#define steering_black 3
#define laser 4
#define left_upper_led A1
#define left_lower_led A0
#define right_upper_led 7
#define right_lower_led 8

/*
ENGINE MOTOR 
Pinout
G - Vdd
Y - Gnd
B - Dir 1
R - Dir 2

Protocol
BR
00 Still
01 Forwards
10 Backwards
11 Unused

STEERING MOTOR 
Pinout
G - Vdd
Y - Dir 1
B - Dir 2
R - Gnd

Protocol
YB
00 Still
01 Left
10 Right
11 Unused
*/

int engine_motor[2], steering_motor[2], headlights[4];

void setup(){
  engine_motor[0] = engine_black;
  engine_motor[1] = engine_red;
  
  steering_motor[0] = steering_yellow;
  steering_motor[1] = steering_black;
  
  headlights[0] = left_upper_led;
  headlights[1] = left_lower_led;
  headlights[2] = right_upper_led;
  headlights[3] = right_lower_led;
  
  pinMode(engine_motor[0], OUTPUT);
  pinMode(engine_motor[1], OUTPUT);
  pinMode(steering_motor[0], OUTPUT);
  pinMode(steering_motor[1], OUTPUT);
  pinMode(headlights[0], OUTPUT);
  pinMode(headlights[1], OUTPUT);
  pinMode(headlights[2], OUTPUT);
  pinMode(headlights[3], OUTPUT);
  
  Serial.begin(19200);
}

void loop(){
    //Do nothing, wait for serial interrupt
}

void serialEvent(){
   //Read 7 characters, then check if it's a valid command.
   //Would be better to use some kind of timeout as well to avoid
   //desyncing, but I couldn't get it to work.
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

//Command structure is one letter and 
boolean isValidCommand(String cmd){
  if (cmd.length() == 7){
    char cmd_type = cmd[0];
    switch (cmd_type){
      case 'F': //Forward
      case 'B': //Backward
      case 'L': //Left
      case 'R': //Right
        {
          //Read the argument. Only the first group of 3 matters.
          int cmd_arg = cmd.substring(1,4).toInt();
          if (cmd_arg <= 255){
            Serial.print("K"); //Argument looks OK, send ack
            return true;
          }
        }
        break; //If not, break and send error message
      case 'S': //Stop
        //Always correct, since the arguments doesn't matter.
        Serial.print("K"); //Argument looks OK, send ack
        return true;
      case 'H': //Lamps
        //The first four numbers must be 0 or 1
        for (int i=0; i<4; i++){
          char value = cmd[i+1];
          if (value != '0' && value != '1'){
            Serial.print("F"); //Something wrong, notify sender
            return false;
          }
        }
        Serial.print("K"); //Argument looks OK, send ack
        return true;
      default:
        break;  //Bad command type
    }
  }
  Serial.print("F"); //Something wrong, notify sender
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
      case 'H': //Extra (for non-movement stuff)
        for (int i=0; i<4; i++){
          char led_val = cmd[i+1];
          if (led_val == '0')
            digitalWrite(headlights[i], LOW);
          else
            digitalWrite(headlights[i], HIGH);
        }
        
        break;  //command type OK, move on to check arguments
      default:
        return; //This shouldn't happen
  }
}

void set_motor_value(int motor[], int val1, int val2){
  analogWrite(motor[0], val1);
  analogWrite(motor[1], val2);
}
