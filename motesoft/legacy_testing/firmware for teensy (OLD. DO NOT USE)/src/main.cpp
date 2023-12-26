
#include <Arduino.h>
#include <NativeEthernet.h>
#include <NativeEthernetUdp.h>

#include <PWMServo.h>


// Ethernet config
byte mac[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED};
IPAddress local_ip(192, 168, 1, 177);
IPAddress remote_ip(192, 168, 1, 123);

unsigned int localPort = 8888; // local port to listen on
unsigned int remotePort = localPort;



//This probably should be in a file shared with the GUI python code
enum ActuatorType {
	Servo,
	GPIO, //solenoid, ignition, and general purpose ctrl pins
};


//global variables
struct received_command {
	int		actuator_id;
	ActuatorType	sensor_type;
	int		value;
} Recieved_command;  

char Sensor_Readings[] = "this is a test"; //TODO later, make this a struct maybe

struct ConfigArray {
	//TODO fill this
} config;

EthernetUDP Udp; // An EthernetUDP instance to let us send and receive packets over UDP
char packetBuffer[UDP_TX_PACKET_MAX_SIZE]; //UDP_TX_PACKET_MAX_SIZE is set to 24 in libraries/NativeEthernet/src/NativeEthernet.h



void read_SD_config(){
	//open config file and parse, and put config in struct ConfigArray
}

//TODO fill all these functions
void read_ADCs(){
	//read values from ADC inputs specified in config struct
	//put values in SendBuffer array (come up with a system of ordering according to config)
}

void read_teensyADCs(){
	//read values from ADC inputs specified in config struct
	//put values in SendBuffer array (come up with a system of ordering according to config)
}

void send_update(char * Sensor_Readings){ //something like this
	Udp.beginPacket(remote_ip, remotePort);
	Udp.write(Sensor_Readings);
	Udp.endPacket();
}


void set_servo(int actuator_id, long value)
{
	//Detach any preexisting servos before connecting the current one. 
	myservo.detach();
	myservo.attach(actuator_id);
	myservo.write(value);
}


void set_GPIO(int actuator_id, int value){ //includes solenoids, ignition, and general purpose output
	//TODO look up pin number for actuator in config, and set pin level
}


void setup_ethernet(){
	Ethernet.begin(mac, local_ip); // start the Ethernet
	if (Ethernet.hardwareStatus() == EthernetNoHardware){ // Check for Ethernet hardware present
		Serial.println("Ethernet shield was not found.	Sorry, can't run without hardware. :(");
		while (true){delay(1);} // do nothing, no point running without Ethernet hardware
	}
	if (Ethernet.linkStatus() == LinkOFF){
		Serial.println("Ethernet cable is not connected.");
	}
	Udp.begin(localPort); // start UDP
}

extern "C" int main(void)
{
	setup_ethernet();
	while (1)
	{
		int packetSize = Udp.parsePacket();
		if (packetSize) { // if recieved actuator command
			Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
			//TODO decode packetBuffer into Recieved_command struct
			switch(Recieved_command.sensor_type) {
				case Servo :
					set_servo(Recieved_command.actuator_id,Recieved_command.value);
					break;
				case GPIO :
					set_GPIO(Recieved_command.actuator_id,Recieved_command.value);
					break;
				}
			//call the aproprate function based on sensor_type, and pass pin number and value as needed
		}
		//loop through all sensors in config, reading from each of them
		send_update(Sensor_Readings); //something like this
	}
}

