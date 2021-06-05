/*
- excerpted this from treadmill_hiddenRewMultTrigMPRrand_012219c.ino

- added array of motor speeds for alternating speed paradigm
- trig pin HIGH during session (started by button)
- sync signal, with LED output
ToDo:
- allow specification of accel/decel profiles
- for fiber runs, don't print pos until session started
- write processing script
- fix track length info
- update rotary encoder code for more frequent updates
- make arrays for motor duration and intervals (or random?)

Doric to be triggered by Arduino:
- Edit any other channel (all in sync) for trigger options --> Source = Digital IO | Ch1 & Mode = Triggered (Normal)
- set Doric Digital I/O Ch1 as treadmill trigger
- set Doric Digital I/O Ch2 as treadmill sync
- set Doric Digital I/O Ch3 as wheel sync
 */


/// VARIABLES TO CHANGE EXPERIMENT PARAMS
String programName = "wheelTreadmill_stefano_041619a";

int isButtonStart = 1;  // this means that prog doesn't print out position data until button is pressed
int useMotor = 1;
int trackLength = 2113; // Stefano: 2113 is the conversion from 900 clicks for 23 in (wheel). Lenght of the treadmill is about 54 in. 900/23x54=2113

int motorArr[] = {98, 122, 156, 190};  // motor speed from 0-255 (increase by 34)
int cycleLength = 5; // length of above array, the motor cycle length (how many of those speeds/array are covered in the protocol)

// motor params
int defMotorVal = 64; // default motor speed, 0-255
int motorVal = 64;
long initMotorTime = 60000; // init time at motor default speed
long motorDur = 60000;
long motorIntv = 60000; // length of motor interval 10000=10seconds (motor interval = each one of the array)

// sync pulse params
int syncDur = 500;  // duration of pulse
int syncIntv = 5000;  // interval of pulse train


// pins
int motorPin1 = 5;
int spkrPin = 47;
int ledPin = 13;

int buttonPin1 = 33;
int trigPin = 52;  // pin for triggering nVista imaging
int syncPin = 53; // pin for nVista sync
int syncPin2 = 49;  // LED for video sync

// times
long startTime = 0;
long endTime = 0;

//
int currPos = 0;
int prevPos = 0;
int dy = 0;
float vel = 0;


// rotary encoder serial input variables
char inMess;
char outMess;

String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete

int yInd = 0;
int mInd = 0;
String dyStr = "";
String msStr = "";
long dt = 0;
long reTime = 0;
long prevReTime = 0;
//int currPos = 0;

long motorStartTime = 0;
long lastMotorTime = 0;
int prevMotor = 0;
int motorCycle = 0;

long syncStartTime = 0;
long prevSyncTime = 0;
int prevSync = 0;
long lastSyncTime = 0;

int isCalibrated = 0;
//int trackLength = 900;

long buttonTime = 0;
long prevButtonTime = 0;
int startSession = 0;


// SETUP ///////////////////
void setup()
{
  // set up pins
  //pinMode(spkrPin, OUTPUT);
  pinMode(motorPin1, OUTPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(buttonPin1, INPUT_PULLUP);
  pinMode(syncPin, OUTPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(syncPin2, OUTPUT);
  
  // Open serial communications
  Serial.begin(38400);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Leonardo only
  }
  //Serial.println(programName);

  // set the data rate for the rotary encoder port
  // NOTE: must match the rate of the rotary encoder nano
  Serial3.begin(115200); //(19200);
  pinMode(15, INPUT); // was having problems and a link suggested this
  digitalWrite(15, HIGH);
  //Serial3.println("Hello, world?");// reserve 200 bytes for the inputString:
  inputString.reserve(200);

  // Now print out some header information with behavioral program parameters
  Serial.print("programName="); Serial.println(programName);
  Serial.print("isButtonStart=");
  Serial.println(isButtonStart);
  Serial.println("END HEADER");

  randomSeed(analogRead(A4));

  analogWrite(motorPin1, 0);
  
}  // end SETUP

// start LOOP  ///////////////////////////
void loop() // run over and over
{
    // read rotary encoder input
    serialEvent1(); //call the function
    
//    // print the string when a newline arrives:
//    if (stringComplete) {
//      //Serial.println(inputString);
//      updatePosition();  // update position and see if this is a reward zone
//      
//      // clear the string:
//      inputString = "";
//      stringComplete = false;
//    }
      

    if (isButtonStart == 1) {
      checkButton();
    }
    if (startSession == 1) {
      if (useMotor==1 && (millis()-startTime>= initMotorTime)) {
        checkMotorState();
      }
      checkSyncState();
    }

}  // end LOOP


// SUBFUNCTIONS ////////////////////



// use rotary input to update position (and check if reward zone)
void updatePosition() {

    //prevPos = currPos;
    
    yInd = inputString.indexOf("dy"); // ind of "dy" in rotary encoder message
    mInd = inputString.indexOf("millis");

    dyStr = inputString.substring(yInd+4, mInd-3); 
//    Serial.println(dyStr);
    dy = dyStr.toInt();
    //dy = -dy;  // 121416: reversing direction to match treadmill
    msStr = inputString.substring(mInd+8, inputString.length()-1); 
    reTime = msStr.toInt();
    dt = reTime - prevReTime;
//    Serial.println(dt);
//    Serial.println(reTime);
//    Serial.println(dy);
    prevReTime = reTime;

    vel = float(dy)/float(dt)*1000;
    currPos = prevPos + dy;
    prevPos = currPos;

    if (startSession==1) {
      Serial.println("dy=" + String(dy) + ", millis=" + String(millis()));
      //Serial.println("currPos=" + String(currPos) + ", millis=" + String(millis()));
    }


      if (currPos >= trackLength){ // + 100) {
        prevPos = 0;
      }

}

////////////////////////////////////////////




/////////////////////////////////////
/* ROTARY ENCODER SERIAL INPUT
  SerialEvent occurs whenever a new data comes in the
 hardware serial RX.  This routine is run between each
 time loop() runs, so using delay inside loop can delay
 response.  Multiple bytes of data may be available.
 */
void serialEvent1() {
  while (Serial3.available()) {
    // get the new byte:
    char inChar = (char)Serial3.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      stringComplete = true;
      
      updatePosition();  // update position and see if this is a reward zone
      
      // clear the string:
      inputString = "";
      stringComplete = false;
    }
  }
}

////////////////////////////////////////

//////////////////////////////
void checkButton() {
  if (digitalRead(buttonPin1) == 0) {
    if (millis() - prevButtonTime > 2000) { // only check button again after few sec
    
      if (startSession == 0) {
        startSession = 1;
        startTime = millis();
        digitalWrite(trigPin, HIGH); // trig pin goes HIGH for duration of session
        Serial.print("START SESSION button, millis = ");
        Serial.println(startTime);
        Serial.print("trigTime, millis=");
        Serial.println(startTime);
        prevButtonTime = startTime;
        if (useMotor==1) {
          Serial.print("initMotorTime="); Serial.print(initMotorTime);
          Serial.print(", millis="); Serial.println(millis());
          analogWrite(motorPin1, defMotorVal);
        }
        
      }
      else {
        startSession = 0;
        endTime = millis();
        digitalWrite(trigPin, LOW);
        digitalWrite(syncPin, LOW);
        digitalWrite(syncPin2, LOW);
        analogWrite(motorPin1, 0);
        Serial.print("END session button, millis=");
        Serial.println(endTime);
        prevButtonTime = endTime;
      }
    }
  }
}

//////////////////////////////
void checkSyncState() {
  if (prevSync == 1 && millis()-syncStartTime>=syncDur) {
    digitalWrite(syncPin, LOW);
    digitalWrite(syncPin2, LOW);
    prevSync = 0;
  }
  else if (millis()- lastSyncTime >= syncIntv) {
    digitalWrite(syncPin, HIGH);
    digitalWrite(syncPin2, HIGH);
    syncStartTime = millis();
    Serial.print("syncOut, millis = ");
    Serial.println(syncStartTime);
    lastSyncTime = syncStartTime;
    prevSync = 1;
  }
}

//////////////////////////////
void checkMotorState() {
  if (prevMotor == 1 && millis()-motorStartTime>=motorDur) {
    Serial.print("motorVal=");
    Serial.print(defMotorVal);
    Serial.print(", millis = ");
    Serial.println(millis());
    analogWrite(motorPin1, defMotorVal);
    //analogWrite(motorPin2, defMotorVal);
    prevMotor = 0;
  }
  else if (millis()- lastMotorTime >= motorIntv) {
    motorCycle = motorCycle +1;
    motorVal = motorArr[motorCycle-1]; // choose appropriate motor speed
    analogWrite(motorPin1, motorVal);
    //analogWrite(motorPin2, motorVal);
    motorStartTime = millis();
    Serial.print("motorVal=");
    Serial.print(motorVal);
    Serial.print(", millis = ");
    Serial.println(motorStartTime);
    lastMotorTime = motorStartTime;
    prevMotor = 1;
    if (motorCycle==cycleLength) {motorCycle=0;}  // reset motor speed cycle
  }
}
