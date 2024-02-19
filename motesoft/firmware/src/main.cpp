#include <vector>
#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include <NativeEthernet.h>    // Must use NativeEthernet libraries with Teensy
#include <NativeEthernetUdp.h> // Must use NativeEthernet libraries with Teensy

//#include <RadioLib.h>
#include <Wire.h>

#include "consts.h"
#include "settings.h"

byte* mac;
unsigned int localPort = 8888;
char packetBuffer[64];
std::vector<char> telemetry_to_send;
char moteID;
EthernetUDP Udp;


void write_to_telemetry_array(std::vector<char>& telemetry_to_send, int sensor_reading, int i, int pin_num)
{
	uint8_t byte1 =  sensor_reading & 0x000000ff;
	uint8_t byte2 = (sensor_reading & 0x0000ff00) >> 8;
	uint8_t byte3 = (sensor_reading & 0x00ff0000) >> 16;
	uint8_t byte4 = (sensor_reading & 0xff000000) >> 24;
	telemetry_to_send.push_back((uint8_t)pin_num);
	telemetry_to_send.push_back(byte1);
	telemetry_to_send.push_back(byte2);
	telemetry_to_send.push_back(byte3);
	telemetry_to_send.push_back(byte4);
}

void setup()
{
    Serial.begin(9600);
    Serial.println("Hello World!");
    moteID = '9';
    Serial.println("Mote number:");
    Serial.println(moteID);
    byte mac1[] = MAC1;
    mac = &mac1[0];

    IPAddress ip(192, 168, 1, 100+moteID-'0');

    Ethernet.begin(mac, ip);
    Serial.println("Began Ethernet!");
    if (Ethernet.hardwareStatus() == EthernetNoHardware)
    {
        Serial.print("Ethernet shield was not found. Cannot run without hardware.\n");
        while (true)
        {
            delay(1); // do nothing, no point running without Ethernet hardware
        }
    }

    Serial.println("After ethernet!");
    while (Ethernet.linkStatus() == LinkOFF)
    {
        Serial.print("Ethernet cable is not connected.");
        delay(1000);
    }

    // Start UDP
    Serial.println("Starting UDP!");
    Udp.begin(localPort);
    Serial.println(Ethernet.localIP());
}

void loop()
{
    int packetSize = Udp.parsePacket();

    if (packetSize)
    {
        IPAddress remote = Udp.remoteIP();
        for (int i = 0; i < 4; i++)
        {
            Serial.print(remote[i], DEC);
            if (i < 3)
            {
                Serial.print(".");
            }
        }
    }else{

      write_to_telemetry_array(telemetry_to_send,random(0,101),0,98); 

      if (Udp.remoteIP()){
  	    Udp.beginPacket(Udp.remoteIP(), 8888);
        Udp.write(telemetry_to_send.data(), telemetry_to_send.size());
  	    Udp.endPacket();
      }
      telemetry_to_send.clear();
      
      delay(1000);
  	}
}