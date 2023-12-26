#include <vector>
#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include <NativeEthernet.h>    // Must use NativeEthernet libraries with Teensy
#include <NativeEthernetUdp.h> // Must use NativeEthernet libraries with Teensy
//#include <Servo.h>
#include <..\..\firmware_for_teensy_USEME\sensors_and_servos.h>
#include <SparkFun_ADS122C04_ADC_Arduino_Library.h>

// TODO: we need to make sure the mac addresses don't overlap
byte mac[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED};

unsigned int localPort = 8888; // Local port to listen on

// Buffers for receiving and sending data
char packetBuffer[64];
char replyBuffer[] = "acknowledged";

// Bool to indicate recieve or transmit data
// TRUE for Rx - FALSE for Tx
// bool RxTx = true;


struct SingleSensorConfig {
  uint8_t pin_num;
  uint8_t interface_type_number;
  SFE_ADS122C04 adc_obj; //only applies for ADC-based sensors. Ignore for others.
};

std::vector<SingleSensorConfig> all_sensors;
std::vector<uint8_t> telemetry_to_send;

std::vector<Servo> servo_obj;

// Variables for saving received data
bool actuator_write_command;
bool actuator_state;
uint8_t interface_type_number;
uint8_t pin_num;

char moteID;
char *deviceType;
char *interface;
char *humanName;
unsigned int pin;
void parsePacket(char *input);

// An EthernetUDP instance to let us send and receive packets over UDP
EthernetUDP Udp;

// set up variables using the SD utility library functions:
Sd2Card card;
SdVolume volume;
SdFile root;

// Teensy 3.5 & 3.6 & 4.1 on-board: BUILTIN_SDCARD
const int chipSelect = 4.1;

void setup()
{
    // Open serial communications and wait for port to open:
    Serial.begin(9600);
    while (!Serial)
    {
        ; // wait for serial port to connect.
    }

    Serial.println("Hello World!");


    // Last digit of IP Address is MOTE ID
    // Ex: 101 = MOTE ID 1
    IPAddress ip(192, 168, 1, 100+moteID);
    // Start the Ethernet
    Ethernet.begin(mac, ip);

    if (Ethernet.hardwareStatus() == EthernetNoHardware)
    {
        Serial.print("Ethernet shield was not found. Cannot run without hardware.\n");
        while (true)
        {
            delay(1); // do nothing, no point running without Ethernet hardware
        }
    }

    Serial.println("After ethernet!");

    if (Ethernet.linkStatus() == LinkOFF)
    {
        Serial.print("Ethernet cable is not connected.");
    }

    Serial.print("\nInitializing SD card...");

    // we'll use the initialization code from the utility libraries
    // since we're just testing if the card is working!
    
    if (!SD.begin(chipSelect))
    {
        Serial.println("initialization failed. Things to check:");
        Serial.println("[+] is a card inserted?");
        Serial.println("[+] is your wiring correct?");
        Serial.println("[+] did you change the chipSelect pin to match your shield or module?");
        Serial.println("[+] is the SD card formatted in FAT32?");
        return;
    }
    Serial.println("Wiring is correct and a card is present.");
    
    card.init(SPI_HALF_SPEED, chipSelect);

    // Now we will try to open the 'volume'/'partition' - it should be FAT16 or FAT32
    if (!volume.init(card))
    {
        Serial.println("Could not find FAT16/FAT32 partition.\nMake sure you've formatted the card");
        return;
    }

    Serial.println("\nFiles found on the card (name, date and size in bytes): ");
    root.open("/"); // DO NOT USE root.openRoot(volume); - deprecated

    // list all files in the card with date and size
    root.ls(LS_R | LS_DATE | LS_SIZE);
    root.close();
  
    // Open the mote_number.txt file and save to moteID
    root.open("/mote_number.txt");
    moteID = root.read();
    Serial.println("Mote number:");
    Serial.println(moteID);
    

    // Start UDP
    Serial.println("Starting UDP!");
    Udp.begin(localPort);
}

void loop()
{
    // if there's data available, read a packet
    int packetSize = Udp.parsePacket();
    if (packetSize)
    {
        Serial.print("Received packet of size ");
        Serial.println(packetSize);
        Serial.print("From ");
        IPAddress remote = Udp.remoteIP();
        for (int i = 0; i < 4; i++)
        {
            Serial.print(remote[i], DEC);
            if (i < 3)
            {
                Serial.print(".");
            }
        }
        Serial.print(", port ");
        Serial.println(Udp.remotePort());

        // read the packet into packetBufffer
        Udp.read(packetBuffer, 64);
        //Serial.println("Contents:");
        //Serial.println(packetBuffer);
        parsePacket(packetBuffer);
        /*if (packetBuffer[0] == moteID)
        {*/
            //Serial.println("\n");
            //Serial.print(packetBuffer[0]);
            //Serial.print(",");
            //Serial.print(packetBuffer[1]);

            

            // send a reply to the IP address and port that sent us the packet we received
            /*
            Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
            Udp.write(replyBuffer);
            Udp.endPacket();
            */
       /* }
        else
        {
            memset(packetBuffer, 0, 64);
            Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
            Udp.write(replyBuffer);
            Udp.endPacket();
        }*/
        delay(10);
    }else{  // Read sensors and send data (if we don't have actuator commands to run now)
            int i = 0;
	    for(SingleSensorConfig sensor : all_sensors){
	    	if(sensor.interface_type_number == 1){ // Teensy ADC
	    		//TODO read the Teensy adc sensor.pin_num
	    		//TODO put that reading into 'int sensor_reading' to prep for next line

                //argument NULL not actually used in code. Don't know why that's there.
                int reading = teensy_analog_read(sensor.pin_num, NULL);
	    		write_to_telemetry_array(telemetry_to_send,reading,i,sensor.pin_num);
	    	}else if(sensor.interface_type_number == 2){ // i2c ADC 1 channel
                //for an explanation of the screwed up pin numbers, see fakeMote.py
                uint32_t reading = i2c_adc_1_wire(sensor.adc_obj, (64 + sensor.pin_num - 42), (sensor.pin_num - 42)%4);
	    		write_to_telemetry_array(telemetry_to_send,reading,i,sensor.pin_num);
	    	}else if(sensor.interface_type_number == 3){ // i2c ADC 2 channel
	    		//TODO read 2 channel ADC sensor.pin_num
                uint32_t reading = i2c_adc_2_wire(sensor.adc_obj, (64 + sensor.pin_num - 42));
	    		write_to_telemetry_array(telemetry_to_send,reading,i,sensor.pin_num);
	    	}else if(sensor.interface_type_number == 4){ // FlowMeter
	    		//TODO read flowmeter sensor.pin_num
	    		write_to_telemetry_array(telemetry_to_send,flowmeter_read_wrapper(),i,sensor.pin_num);
	    	}else{
		    	Serial.println("Error. Interface number is not valid");
	    	}
	    	i++;
	    }
	    Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
	    Udp.write(telemetry_to_send);
	    Udp.endPacket();

	}
}

void write_to_telemetry_array(std::vector<uint8_t>& telemetry_to_send, int sensor_reading, int i, int pin_num)
{
	uint8_t byte1 =  sensor_reading & 0x000000ff;
	uint8_t byte2 = (sensor_reading & 0x0000ff00) >> 8;
	uint8_t byte3 = (sensor_reading & 0x00ff0000) >> 16;
	uint8_t byte4 = (sensor_reading & 0xff000000) >> 24;
	telemetry_to_send[5*i] = pin_num;
	telemetry_to_send[5*i+1] = byte1;
	telemetry_to_send[5*i+2] = byte2;
	telemetry_to_send[5*i+3] = byte3;
	telemetry_to_send[5*i+4] = byte4
}

void parsePacket(char *data)
{
    pin_num = data[0];
    uint8_t config_byte = data[1];
    actuator_write_command = (config_byte & 0b10000000) == 0b10000000;
    actuator_state = (config_byte & 0b01000000) == 0b01000000;
    interface_type_number = (config_byte & 0b00111111);

    if (actuator_write_command)
    {
      Serial.print("Setting pin ");
      Serial.print(pin_num);
      Serial.print(" to ");
      Serial.print(actuator_state);
      Serial.print(" with interface ");
      if (interface_type_number == 5)
      {
          Serial.println("servoPWM");
          //TODO: set servo pin_num to actuator_state
          servo_write(Servo(), pin_num, actuator_state);
      }
      else if (interface_type_number == 6){
          Serial.println("Binary GPIO");
          //TODO: set GPIO pin_num to actuator_state
          analog_write(pin_num, actuator_state);
      }
      else
      {
        Serial.println("Error. Interface number is not valid");
      }
    }else{  // if a sensor config command, save the sensor config
    	SingleSensorConfig new_sensor;
    	new_sensor.pin_num = pin_num;
    	new_sensor.interface_type_number = interface_type_number; 
    	all_sensors.push_back(new_sensor);

    	if(new_sensor.interface_type_number == 1){ // Teensy ADC
    		//TODO configure the Teensy adc (using new_sensor.pin_num)
    	}else if(new_sensor.interface_type_number == 2){ // i2c ADC 1 channel
    		//TODO configure 1 channel ADC (using new_sensor.pin_num)
    	}else if(new_sensor.interface_type_number == 3){ // i2c ADC 2 channel
    		//TODO configure 2 channel ADC (using new_sensor.pin_num)
    	}else if(new_sensor.interface_type_number == 4){ // FlowMeter
    		//TODO configure flowmeter (using new_sensor.pin_num)
    	}else{
	    	Serial.println("Error. Interface number is not valid");
    	}
    }
}
