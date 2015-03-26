# Introduction #

Arduino is a great open-source microcontroller platform to use with the XIG. Here are two very basic examples of how to send and receive information using simple URLs. For the web server side, we'll show PHP example code. Rails, Python or any other web application language can be used the same way.


# Details #

Download Arduino
```
/*
 * *********XBee Internet Gateway Download Example********
 * by Rob Faludi http://faludi.com
 */

#define NAME "XIG Download Example"
#define VERSION "1.00"

int outputLED = 9; // define pin 9 as a PWM analog output light

void setup() {
  Serial.begin(115200); // faster is better for XIG
  pinMode(outputLED, OUTPUT);
}

void loop() {
  if (millis() % 1000 == 0) {  // wait a second before sending the next request
    // request the current value
    Serial.println("http://<your server URL here>/XIG_download_example.php");
  }
  if (Serial.available() > 0) { // if there's a byte waiting
    int value = Serial.read(); // read a single byte

    analogWrite(value, outputLED); // write the 
	// *** SOMETHING MORE USEFUL CAN BE DONE WITH THIS VALUE VARIABLE HERE ***  

  }
}
```


Download PHP
```
<?php
	// xig_download_example.php
	// this code posts a simple value in ASCII when the page is loaded
	$value = "8";
	echo $value;
?>
```
Upload Arduino
```
/*
 * *********XBee Internet Gateway Upload Example********
 * by Rob Faludi http://faludi.com
 */

#define NAME "XIG Upload Example"
#define VERSION "1.00"
#define LED_PIN 13

int inputPin = 0;

void setup() {
  pinMode(LED_PIN,OUTPUT);
  blinkLED(LED_PIN,2,100);
  Serial.begin(115200); // faster is better for XIG
  delay(2000);
}


void loop() {
  // read the analog pin
  int value = analogRead(inputPin);
  // upload the current value to the server, it will be stored in a dataFile.txt
  Serial.print("<YOUR-SERVER-HERE>/xig_upload_example.php?value=");
  Serial.println(value, DEC);
  // wait a second between uploads
  delay(1000);
  blinkLED(LED_PIN,1,100);
}


////////////////// UTILITIES //////////////////
// this function blinks the an LED light as many times as requested, at the requested blinking rate
void blinkLED(byte targetPin, int numBlinks, int blinkRate) {
  for (int i=0; i<numBlinks; i++) {
    digitalWrite(targetPin, HIGH);   // sets the LED on
    delay(blinkRate);                     // waits for blinkRate milliseconds
    digitalWrite(targetPin, LOW);    // sets the LED off
    delay(blinkRate);
  }
}
```


Upload PHP
```
<?php
	// xig_upload_example.php
	// this code accepts any data uploaded as a GET variable and stores it
	//  into a text file called dataFile.txt on the server
	
	$value = $_GET['value'];
	$myFile = "dataFile.txt";
	$fh = fopen($myFile, 'a') or die("can't open file");
	fwrite($fh, $value);
	fwrite($fh, "\n");
	fclose($fh);
?>
```

In most cases there's no need to use the XBee's API mode at all with the XIG. However, if your application requires the API for other reasons, here's an example which will work fine in that mode. It uses the [XBee Arduino library](http://code.google.com/p/xbee-arduino/) and was contributed by Steven Race:

API example
```
//Arduino Code
#include <XBee.h> 
#include <string.h>

XBee xbee = XBee(); 
char basehtml[30] = "http://foo.com/bar\r\n";

XBeeAddress64 addr64 = XBeeAddress64(0x00000000, 0x0000ffff); 
ZBTxRequest zbTx = ZBTxRequest(addr64, (uint8_t*) (basehtml), strlen(basehtml)); 

void setup() {
  xbee.begin(9600);
  Serial.begin(9600);
  } 

void loop() { 
  Serial.println("http://foo.com/bar"); // as used in the example, this doesn't work
  xbee.send(zbTx);  // this returns 'RECV...' message above

  delay(1000); } 
```