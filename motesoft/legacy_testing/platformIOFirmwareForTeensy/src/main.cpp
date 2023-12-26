
// This is code from "firmware for teensy" meant to work with platformIO. We can't all be linux wizards :/

#include <Arduino.h>
#include <NativeEthernet.h>
#include <NativeEthernetUdp.h>
#include <PWMServo.h>

// Global variables because making a class for this is not the move
// Can you even make classes in Arduino???
// Note to self: look at exeggutor code to see how they did it
PWMServo myservo;

void setup()

{
  // Test: do you get a 3.3v high?
  int highPin = 2;
  pinMode(highPin, OUTPUT);
  digitalWrite(highPin, HIGH);
  //set pin 10 as the servo pin
  myservo.attach(10); //On teensy4.1, we can use these pins for servos: 0-15, 18-19, 22-25, 28-29, 33, 36-37
  //use this python line to calculate the expected duty for a given angle
  //angle=90;min=544;max=2400;us=(int((max/16 - min/16) * 46603 * angle) >> 11) + (int(min/16) << 12); print(f'duty is {(us * 3355) >> 22} out of 4095 for angle {angle}')

  /* Ethernet test code in progress, a lot of it is duplicated below
  // Enter a MAC address and IP address for your controller below.
  // The IP address will be dependent on your local network:
  byte mac[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED};
  IPAddress local_ip(192, 168, 1, 177);
  IPAddress remote_ip(192, 168, 1, 123);

  unsigned int localPort = 8888; // local port to listen on
  unsigned int remotePort = localPort;

  char ReplyBuffer[] = "this is a test";

  // An EthernetUDP instance to let us send and receive packets over UDP
  EthernetUDP Udp;

  // start the Ethernet
  Ethernet.begin(mac, local_ip);

  // Check for Ethernet hardware present
  if (Ethernet.hardwareStatus() == EthernetNoHardware)
  {
    Serial.println("Ethernet shield was not found.	Sorry, can't run without hardware. :(");
    while (true)
    {
      delay(1); // do nothing, no point running without Ethernet hardware
    }
  }
  if (Ethernet.linkStatus() == LinkOFF)
  {
    Serial.println("Ethernet cable is not connected.");
  }

  // start UDP
  Udp.begin(localPort);
  */
}
void loop()
{
  // servo goes 180 degrees in one direction
  for (int pos = 0; pos < 180; pos++)
  {
    myservo.write(pos);
    delay(15);
  }
  // then go the other direction
  for (int pos = 180; pos > 0; pos--)
  {
    myservo.write(pos);
    delay(15);
  }
  /* Ethernet test code in progress
  EthernetUDP Udp;
  byte mac[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED};
  IPAddress local_ip(192, 168, 1, 177);
  IPAddress remote_ip(192, 168, 1, 123);

  unsigned int localPort = 8888; // local port to listen on
  unsigned int remotePort = localPort;
  char ReplyBuffer[] = "this is a test";
  // send a reply to the IP address and port that sent us the packet we received
  Udp.beginPacket(remote_ip, remotePort);
  Udp.write(ReplyBuffer);
  Udp.endPacket();
  //delay(10);
  */
}

/*
extern "C" int main(void){
	// Enter a MAC address and IP address for your controller below.
	// The IP address will be dependent on your local network:
	byte mac[] = {
		0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
	};
	IPAddress ip(192, 168, 1, 177);

	unsigned int localPort = 8888;			// local port to listen on

	// buffers for receiving and sending data
	char packetBuffer[UDP_TX_PACKET_MAX_SIZE];	// buffer to hold incoming packet,
	char ReplyBuffer[] = "acknowledged";				// a string to send back

	// An EthernetUDP instance to let us send and receive packets over UDP
	EthernetUDP Udp;
	
	
	// You can use Ethernet.init(pin) to configure the CS pin
	//Ethernet.init(10);	// Most Arduino shields
	//Ethernet.init(5);	 // MKR ETH shield
	//Ethernet.init(0);	 // Teensy 2.0
	//Ethernet.init(20);	// Teensy++ 2.0
	//Ethernet.init(15);	// ESP8266 with Adafruit Featherwing Ethernet
	//Ethernet.init(33);	// ESP32 with Adafruit Featherwing Ethernet

	// start the Ethernet
	Ethernet.begin(mac, ip);

	// Open serial communications and wait for port to open:
	Serial.begin(9600);
	while (!Serial) {
		; // wait for serial port to connect. Needed for native USB port only
	}

	// Check for Ethernet hardware present
	if (Ethernet.hardwareStatus() == EthernetNoHardware) {
		Serial.println("Ethernet shield was not found.	Sorry, can't run without hardware. :(");
		while (true) {
			delay(1); // do nothing, no point running without Ethernet hardware
		}
	}
	if (Ethernet.linkStatus() == LinkOFF) {
		Serial.println("Ethernet cable is not connected.");
	}

	// start UDP
	Udp.begin(localPort);


	while(1){
		// if there's data available, read a packet
		int packetSize = Udp.parsePacket();
		if (packetSize) {
			Serial.print("Received packet of size ");
			Serial.println(packetSize);
			Serial.print("From ");
			IPAddress remote = Udp.remoteIP();
			for (int i=0; i < 4; i++) {
				Serial.print(remote[i], DEC);
				if (i < 3) {
					Serial.print(".");
				}
			}
			Serial.print(", port ");
			Serial.println(Udp.remotePort());

			// read the packet into packetBufffer
			Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
			Serial.println("Contents:");
			Serial.println(packetBuffer);

			// send a reply to the IP address and port that sent us the packet we received
			Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
			Udp.write(ReplyBuffer);
			Udp.endPacket();
		}
		delay(10);
	}

}
*/
