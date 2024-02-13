#include <vector>
#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include <NativeEthernet.h>    // Must use NativeEthernet libraries with Teensy
#include <NativeEthernetUdp.h> // Must use NativeEthernet libraries with Teensy
#include <PWMServo.h>
#include <sensors_and_servos.h>
#include <SparkFun_ADS122C04_ADC_Arduino_Library.h>
#include <Wire.h>

#include "consts.h"
#include "settings.h"

byte* mac;

unsigned int localPort = PORT; // Local port to listen on

// Buffers for receiving and sending data
char packetBuffer[64];
//char replyBuffer[] = "acknowledged";

// Bool to indicate recieve or transmit data
// TRUE for Rx - FALSE for Tx
// bool RxTx = true;

SFE_ADS122C04* temp;

AD7193_arg_t spi_adc_config_1;
AD7193_arg_t spi_adc_config_2;

struct SingleSensorConfig {
  uint8_t pin_num;
  uint8_t interface_type_number;
  SFE_ADS122C04* adc_ptr;
};

std::vector<SingleSensorConfig> all_sensors;
std::vector<char> telemetry_to_send;

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
const int chipSelect = BUILTIN_SDCARD;

//which solenoids to set OPEN/CLOSE on startup
//These are the pins mapped to CTRL 1-6 and SOLENOID 1-6 on the schematic
int solenoid_pins[] = {};
int inverse_solenoid_pins_mote1[] = MOTE1_INITIALLY_POWERED_SOLENOIDS;
int inverse_solenoid_pins_mote2[] = MOTE2_INITIALLY_POWERED_SOLENOIDS;
int inverse_solenoid_pins_mote3[] = MOTE3_INITIALLY_POWERED_SOLENOIDS;

int loop_delay_ms = 1;
uint64_t ticks = 0;

bool do_fireX = DO_FIREX;
bool hot_fireX = false;

//IN MILLISECONDS. IF YOU SET IT IN SECONDS, MINUTES, HOURS, ETC, YOU WILL HAVE A BAD TIME!
unsigned long cold_fireX_time;
unsigned long cold_fireX_delay = COLD_FIREX_TIME_DEFAULT; //fake number
unsigned long hot_fireX_time;
unsigned long hot_fireX_delay = HOT_FIREX_TIME_DEFAULT;

//bang-bang control bools
bool do_bang_bang_ox = false;
bool do_bang_bang_fuel = false;

//TODO make this read from a file instead of hardcoded
//Bang-Bang config data
bool VENT_OX_flag = false;
bool PRESS_OX_flag = false;
bool VENT_FUEL_flag = false;
bool PRESS_FUEL_flag = false;

//bullshit pin nums, replace with real ones or config file system
int PRESS_OX_pin_nums[] = NO2_PRESS_PIN_NUM; //MOSFET J34
int VENT_OX_pin_nums[] = NO2_VENT_PIN_NUM; //MOSFET J33
int PRESS_FUEL_pin_nums[] = IPA_PRESS_PIN_NUM; //MOSFET J30
int VENT_FUEL_pin_nums[] = IPA_VENT_PIN_NUM; //MOSFET J7

int sensor_ox_pin_num = NO2_SENSOR_PIN_NUM;
SFE_ADS122C04* ox_adc_ptr;
int sensor_fuel_pin_num = IPA_SENSOR_PIN_NUM;
SFE_ADS122C04* fuel_adc_ptr;

void write_to_telemetry_array(std::vector<char>& telemetry_to_send, int sensor_reading, int i, int pin_num)
{
  //Serial.println("Starting write_to_telemetry_array");
  //telemetry_to_send.resize(telemetry_to_send.size()+5);
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

void hot_fail(){
  if (moteID == '3'){
    digital_write(FIREX_PIN_NUM, false);

    for (int n : VENT_FUEL_pin_nums){
      digital_write(n, false);
    }

    for (int n : VENT_OX_pin_nums){
      digital_write(n, false);
    }
  }

    if (moteID == '1')
      for (int pin : inverse_solenoid_pins_mote1){
          digital_write(pin, false);
      }
    if (moteID == '2')
      for (int pin : inverse_solenoid_pins_mote2){
          digital_write(pin, false);
      }
    if (moteID == '3')
      for (int pin : inverse_solenoid_pins_mote2){
          digital_write(pin, false);
      }
}

void cold_fail(){
  digital_write(FIREX_PIN_NUM, false);
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
      #ifdef ENABLE_DEBUG
        Serial.print("Setting pin ");
        Serial.print(pin_num);
        Serial.print(" to ");
        Serial.print(actuator_state);
        Serial.println(" with interface ");
      #endif
      if (interface_type_number == PWM_SERVO)
      {
          int servo_angle = 0;
          if (actuator_state){
            servo_angle = 180;
          } else {
            servo_angle = 0;
          }
          #ifdef ENABLE_DEBUG
            Serial.println("servoPWM");
            Serial.print("Pin num: ");
            Serial.println(pin_num);
            Serial.print("State: ");
            Serial.println(servo_angle);
          #endif
          //TODO: set servo pin_num to actuator_state
          servo_write(PWMServo(), pin_num, servo_angle);
      }
      else if (interface_type_number == BINARY_LOAD_SWITCH){
          //pinMode(pin_num, OUTPUT);
          //digitalWrite(pin_num, LOW);
          digital_write(pin_num, actuator_state);
      } 
      else if (interface_type_number == BANG_BANG_CONTROL){
        #ifdef ENABLE_DEBUG
        Serial.println("toggle bang-bang");
        Serial.println(pin_num);
        Serial.println(actuator_state);
        #endif
  
        if(pin_num == 1){
          do_bang_bang_ox = actuator_state;
          if (!do_bang_bang_ox){
            Serial.println("Shutting all bang-bang valves.");
            for (int n : VENT_OX_pin_nums){
              digital_write(n, false);
            }
            for (int n : PRESS_OX_pin_nums){
              digital_write(n, false);
            }
          }
        }
        if(pin_num == 0){
          do_bang_bang_fuel = actuator_state;
          if (!do_bang_bang_fuel){
            Serial.println("Shutting all bang-bang valves.");
            for (int n : VENT_FUEL_pin_nums){
              digital_write(n, false);
            }
            for (int n : PRESS_FUEL_pin_nums){
              digital_write(n, false);
            }
          }
        }
      }
      else if (interface_type_number == AUTO_FIREX_CONTROL){
        hot_fireX = actuator_state;
        Serial.print("Set HOT_FIREX to: ");
        Serial.println(hot_fireX);
      }
      else if (interface_type_number == HEARTBEAT){
        Serial.println("Heartbeat recieved");
      }
      else
      {
        Serial.println(interface_type_number);
        Serial.println("Error. Actuator Interface number is not valid");
      }
      //ACK HERE
      if(interface_type_number != HEARTBEAT && interface_type_number != AUTO_FIREX_CONTROL && interface_type_number != BANG_BANG_CONTROL) 
        write_to_telemetry_array(telemetry_to_send, (int)actuator_state, 0, pin_num + 100);
      //End ACK
    }else{  // if a sensor config command, save the sensor config
      Serial.println("Recieved a sensor config command");
    	SingleSensorConfig new_sensor;
    	new_sensor.pin_num = pin_num;
    	new_sensor.interface_type_number = interface_type_number; 
    	
    	if(new_sensor.interface_type_number == TEENSY_ADC){ 
        // Interal Teensy ADC. No-op.
    	}else if(new_sensor.interface_type_number == I2C_ADC_1CH || new_sensor.interface_type_number == I2C_ADC_2CH || new_sensor.interface_type_number == INTERNAL_TEMP ||
    	        (new_sensor.interface_type_number >= I2C_ADC_2CH_MIN_GAIN && new_sensor.interface_type_number <= I2C_ADC_2CH_MAX_GAIN)){ // i2c ADC
        new_sensor.adc_ptr = new SFE_ADS122C04;
        new_sensor.adc_ptr->begin((new_sensor.pin_num/10 + 64), Wire);

        new_sensor.adc_ptr->setDataRate(ADS122C04_DATA_RATE_1000SPS);
        //TURBO MODE
        //HELL YEAH
        new_sensor.adc_ptr->setOperatingMode(ADS122C04_OP_MODE_TURBO);

        
        Serial.println("Began ADC!");
    	}else if(new_sensor.interface_type_number == FLOWMETER){ // FlowMeter
    		//TODO configure flowmeter (using new_sensor.pin_num)
      }
      else if (new_sensor.interface_type_number == SPI_ADC_1CH) {
        if (new_sensor.pin_num / 10 == 0) {
          spi_adc_config_1.channel_bits |= (1 << (new_sensor.pin_num % 10)) << 8;
          spi_adc_config_1.differential = false;
          spi_adc_config_1.internal_temp = false;
          spi_adc_config_1.pga_gain = 1;
          spi_adc_config_1.spi_num = 0;
          configure_AD7193(spi_adc_config_1);
        } else {
          spi_adc_config_2.channel_bits |= (1 << (new_sensor.pin_num % 10)) << 8;
          spi_adc_config_2.differential = false;
          spi_adc_config_2.internal_temp = false;
          spi_adc_config_2.pga_gain = 1;
          spi_adc_config_2.spi_num = 1;
          configure_AD7193(spi_adc_config_2);
        }
      } else if (new_sensor.interface_type_number >= SPI_ADC_2CH && new_sensor.interface_type_number <= SPI_ADC_2CH_MAX_GAIN) {
        if (new_sensor.pin_num / 10 == 0) {
          spi_adc_config_1.channel_bits |= (1 << (new_sensor.pin_num % 10)) << 8;
          spi_adc_config_1.differential = true;
          spi_adc_config_1.internal_temp = false;
          spi_adc_config_1.pga_gain = (int)pow(2, new_sensor.interface_type_number - SPI_ADC_2CH);
          spi_adc_config_1.spi_num = 0;
          configure_AD7193(spi_adc_config_1);
        } else {
          spi_adc_config_2.channel_bits |= (1 << (new_sensor.pin_num % 10)) << 8;
          spi_adc_config_2.differential = true;
          spi_adc_config_2.internal_temp = false;
          spi_adc_config_2.pga_gain = (int)pow(2, new_sensor.interface_type_number - SPI_ADC_2CH);
          spi_adc_config_2.spi_num = 1;
          configure_AD7193(spi_adc_config_2);
        }
      } else if (new_sensor.interface_type_number == INTERNAL_TEMP) {
        if (new_sensor.pin_num / 10 == 0) {
          spi_adc_config_1.channel_bits = (1 << 0b1000) << 8;
          spi_adc_config_1.differential = false;
          spi_adc_config_1.internal_temp = true;
          spi_adc_config_1.pga_gain = 1;
          spi_adc_config_1.spi_num = 0;
          configure_AD7193(spi_adc_config_1);
        } else {
          spi_adc_config_2.channel_bits = (1 << 0b1000) << 8;
          spi_adc_config_2.differential = false;
          spi_adc_config_2.internal_temp = true;
          spi_adc_config_2.pga_gain = 1;
          spi_adc_config_2.spi_num = 1;
          configure_AD7193(spi_adc_config_2);
        }
      }
      else if (new_sensor.interface_type_number == SENSOR_CLEAR_CODE) {
        all_sensors.clear();
        return;
    	}else{
	    	Serial.println("Error. Interface number is not valid");
    	}
      
      
      all_sensors.push_back(new_sensor);
    }
}

void config_adc(SFE_ADS122C04* mySensor){
  //copied from https://github.com/sparkfun/SparkFun_ADS122C04_ADC_Arduino_Library/blob/main/examples/Qwiic_PT100_ADS122C04/Example9_ManualConfig/Example9_ManualConfig.ino
  mySensor->setInputMultiplexer(ADS122C04_MUX_AIN1_AIN0); // Route AIN1 and AIN0 to AINP and AINN
  mySensor->setGain(ADS122C04_GAIN_1); // Set the gain to 1
  mySensor->enablePGA(ADS122C04_PGA_DISABLED); // Disable the Programmable Gain Amplifier
  mySensor->setDataRate(ADS122C04_DATA_RATE_20SPS); // Set the data rate (samples per second) to 20
  mySensor->setOperatingMode(ADS122C04_OP_MODE_NORMAL); // Disable turbo mode
  mySensor->setConversionMode(ADS122C04_CONVERSION_MODE_SINGLE_SHOT); // Use single shot mode
  mySensor->setVoltageReference(ADS122C04_VREF_INTERNAL); // Use the internal 2.048V reference
  mySensor->enableInternalTempSensor(ADS122C04_TEMP_SENSOR_ON); // Disable the temperature sensor
  mySensor->setDataCounter(ADS122C04_DCNT_DISABLE); // Disable the data counter (Note: the library does not currently support the data count)
  mySensor->setDataIntegrityCheck(ADS122C04_CRC_DISABLED); // Disable CRC checking (Note: the library does not currently support data integrity checking)
  mySensor->setBurnOutCurrent(ADS122C04_BURN_OUT_CURRENT_OFF); // Disable the burn-out current
  mySensor->setIDACcurrent(ADS122C04_IDAC_CURRENT_OFF); // Disable the IDAC current
  mySensor->setIDAC1mux(ADS122C04_IDAC1_DISABLED); // Disable IDAC1
  mySensor->setIDAC2mux(ADS122C04_IDAC2_DISABLED); // Disable IDAC2

  mySensor->enableDebugging(Serial); //Enable debug messages on Serial
  mySensor->printADS122C04config(); //Print the configuration
  mySensor->disableDebugging(); //Enable debug messages on Serial

  mySensor->configureADCmode(ADS122C04_RAW_MODE);

  Serial.println("Configured ADC");
}

/**
 * Unit conversion based on magic ADC numbers.
 * Don't question it.
*/
double adc_to_psi5k(uint32_t val){
  double volts = (val-2147483648)/4096000.0;
  Serial.println(volts);
  double psi = 1250 * 2 * volts - 625;
  return psi;
}

double adc_to_psi1k(uint32_t val){
  double volts = (val-2147483648)/4096000.0;
  Serial.println(volts);
  double psi = 2 * 250 * volts - 125;
  return psi;
}

double adc_to_volt(uint32_t val){
  return (val-2147483648)/4096000.0;
}

void bang_bang(){
  for(SingleSensorConfig sensor : all_sensors){
    if (sensor.pin_num == sensor_ox_pin_num){
      ox_adc_ptr = sensor.adc_ptr;  
    }
    if (sensor.pin_num == sensor_fuel_pin_num){
      fuel_adc_ptr = sensor.adc_ptr;  
    }
  }

  //Serial.println("Taking reading");
  uint32_t ox_reading;
  double ox_pressure;
  uint32_t fuel_reading;
  double fuel_pressure;

  if(do_bang_bang_ox && ox_adc_ptr) {
    ox_reading = i2c_adc_1_wire(ox_adc_ptr, sensor_ox_pin_num/10 + 64, sensor_ox_pin_num%10);
    ox_pressure = adc_to_psi5k(ox_reading);

    //set flags
    if(ox_pressure < OX_PRESS_LOWER_BOUND_PSI){
      PRESS_OX_flag = true;
    }
    if (ox_pressure > OX_PRESS_UPPER_BOUND_PSI){
      PRESS_OX_flag = false;
    }
    if (ox_pressure < OX_CLOSE_VENT_BOUND_PSI){
      VENT_OX_flag = false;
    }
    if (ox_pressure > OX_OPEN_VENT_BOUND_PSI){
      VENT_OX_flag = true;
    }
    for (int n : VENT_OX_pin_nums){
        if (USE_TANK_STAND_SERVOS)
          servo_write(PWMServo(), n, !(VENT_OX_flag ? 180 : 0));
        else
          digital_write(n, !VENT_OX_flag);
    }
    for (int n : PRESS_OX_pin_nums){
        digital_write(n, PRESS_OX_flag);
    }
  } else {
    do_bang_bang_ox = false;  
  }
  
  if(do_bang_bang_fuel && fuel_adc_ptr){
    
    fuel_reading = i2c_adc_1_wire(fuel_adc_ptr, sensor_fuel_pin_num/10 + 64, sensor_fuel_pin_num%10);
    //fuel_pressure = adc_to_psi5k(fuel_reading);
    fuel_pressure = adc_to_psi1k(fuel_reading);
    //set flags
    if(fuel_pressure < FUEL_PRESS_LOWER_BOUND_PSI){
      PRESS_FUEL_flag = true;
    }
    if (fuel_pressure > FUEL_PRESS_UPPER_BOUND_PSI){
      PRESS_FUEL_flag = false;
    }
    if (fuel_pressure < FUEL_CLOSE_VENT_BOUND_PSI){
      VENT_FUEL_flag = false;
    }
    if (fuel_pressure > FUEL_OPEN_VENT_BOUND_PSI){
      VENT_FUEL_flag = true;
    }
    for (int n : VENT_FUEL_pin_nums){
        if (USE_TANK_STAND_SERVOS)
          servo_write(PWMServo(), n, (VENT_FUEL_flag ? 180 : 0));
        else
          digital_write(n, !VENT_FUEL_flag);
    }
    for (int n : PRESS_FUEL_pin_nums){
        digital_write(n, PRESS_FUEL_flag);
    }
  } else {
    do_bang_bang_fuel = false;  
  }
}

void setup()
{
    // Open serial communications and wait for port to open:
    Serial.begin(9600);
    
    Serial.println("Hello World!");

/*
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

  */

    moteID = '1';
   
    Serial.println("Mote number:");
    Serial.println(moteID);

    byte mac1[] = MAC1;
    byte mac2[] = MAC2;
    byte mac3[] = MAC3;
    byte mac4[] = MAC4;

    if (moteID == '1') {
      mac = &mac1[0];
    } else if (moteID == '2') {
      mac = &mac2[0];
    } else if (moteID == '3') {
      mac = &mac3[0];
    }

    // Last digit of IP Address is MOTE ID
    // Ex: 101 = MOTE ID 1
    IPAddress ip(192, 168, 1, 100+moteID-'0');
    Serial.println("Set IP!");
    //IPAddress ip(192, 168, 1, 101);
    // Start the Ethernet

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

    Wire.begin();
    // Set I2C Frequency to maximum.
    Wire.setClock(400000);
    Serial.println("Initialized wire!");

    //status light

    Serial.println("Initializing Solenoids");
    for (int pin : solenoid_pins){
      digital_write(pin, false);
    }
    
  
    if (moteID == '1')
      for (int pin : inverse_solenoid_pins_mote1){
          digital_write(pin, true);
      }
    if (moteID == '2')
      for (int pin : inverse_solenoid_pins_mote2){
          digital_write(pin, true);
      }
    if (moteID == '3')
      for (int pin : inverse_solenoid_pins_mote2){
          digital_write(pin, true);
      }
  
    //this is technically redundant, so it is commented out
    /*
    Serial.println("Shutting all bang-bang valves.");
    for (int n : VENT_pin_nums){
      digital_write(n, false);
    }
    for (int n : PRESS_pin_nums){
      digital_write(n, false);
    }
    */

    hot_fireX_time = millis() + hot_fireX_delay;
    cold_fireX_time = millis() + cold_fireX_delay;
}

void loop()
{
    // if there's data available, read a packet
    int packetSize = Udp.parsePacket();
    //Serial.println(packetSize);
    //Serial.print(" ");
    uint32_t loop_start_time = millis();
    
    if (packetSize)
    {
        #ifdef ENABLE_DEBUG
        Serial.print("Received packet of size ");
        Serial.println(packetSize);
        Serial.print("From ");
        #endif
        
        cold_fireX_time = millis() + cold_fireX_delay;
        hot_fireX_time = millis() + hot_fireX_delay;
        
        IPAddress remote = Udp.remoteIP();
        for (int i = 0; i < 4; i++)
        {
            Serial.print(remote[i], DEC);
            if (i < 3)
            {
                Serial.print(".");
            }
        }
        #ifdef ENABLE_DEBUG
        Serial.print(", port ");
        Serial.println(Udp.remotePort());
        #endif

        // read the packet into packetBufffer
        Udp.read(packetBuffer, 64);
        parsePacket(packetBuffer);
    }else{
      //Serial.println("No packet!"); 
      // Read sensors and send data (if we don't have actuator commands to run now)
      int i = 0;
      //Serial.println(all_sensors.size());
	    for(SingleSensorConfig sensor : all_sensors){
        
        //Serial.println("for loop!");

	    	if(sensor.interface_type_number == TEENSY_ADC){ // Teensy ADC
         
          //argument 0 not actually used in code. Don't know why that's there.
          int reading = teensy_analog_read(sensor.pin_num, 0);
	    		write_to_telemetry_array(telemetry_to_send,reading,i,sensor.pin_num);
	    	}
	    	else if(sensor.interface_type_number == I2C_ADC_1CH){ // i2c ADC 1 channel
          //Serial.println("1ch");
          //for an explanation of the screwed up pin numbers, see fakeMote.py
          //Serial.println(sensor.pin_num/10 + 64);
          uint32_t reading = i2c_adc_1_wire(sensor.adc_ptr, sensor.pin_num/10 + 64, sensor.pin_num%10);
	    		write_to_telemetry_array(telemetry_to_send,reading,i,sensor.pin_num);
	    	}else if(sensor.interface_type_number == I2C_ADC_2CH){
	    	  // i2c ADC 2 channel
	    		//TODO read 2 channel ADC sensor.pin_num
          uint32_t reading = i2c_adc_2_wire(sensor.adc_ptr, sensor.pin_num/10 + 64, sensor.pin_num%10, 0);
          write_to_telemetry_array(telemetry_to_send,reading,i,sensor.pin_num);         
	    	}else if(sensor.interface_type_number == FLOWMETER){ // FlowMeter
	    		//WARNING: This is legacy code and currently does nothing. Re-implement for DL.
	    		write_to_telemetry_array(telemetry_to_send,flowmeter_read_wrapper(),i,sensor.pin_num);
	    	}else if (sensor.interface_type_number >= I2C_ADC_2CH_MIN_GAIN && sensor.interface_type_number <= I2C_ADC_2CH_MAX_GAIN){
          int pga_gain_code = sensor.interface_type_number - 6;
          //Serial.print("PGA gain code: ");
          //Serial.println(pga_gain_code);
          uint32_t reading = i2c_adc_2_wire(sensor.adc_ptr, sensor.pin_num/10 + 64, sensor.pin_num%10,pga_gain_code);
          write_to_telemetry_array(telemetry_to_send,reading,i,sensor.pin_num);
        } else if (sensor.interface_type_number == INTERNAL_TEMP){
          //truncate to nearest int (*C). We can make this sensible if we need more exact temperature values
          //but the noise floor on the thermocouple is so bad this should be fine
          if (ticks % 2000 == 0){
            uint32_t pre_temp_time = millis();
            int reading = (int)(1000 * i2c_adc_internal_temp(sensor.adc_ptr, sensor.pin_num/10 + 64));
            write_to_telemetry_array(telemetry_to_send,reading,i,sensor.pin_num);
            Serial.printf("Temp time: %d ms\n", millis() - pre_temp_time);
          }
        }
        else if (sensor.interface_type_number >= SPI_ADC_1CH && sensor.interface_type_number <= SPI_ADC_2CH_MAX_GAIN) {
          AD7193_reading_t reading;
          if (sensor.pin_num / 10 == 0) {
            reading = read_AD7193(spi_adc_config_1);
          } else {
            reading = read_AD7193(spi_adc_config_2);
          }

          Serial.println(reading.result);
          Serial.println(reading.channel + (10 * (sensor.pin_num/10)));

          write_to_telemetry_array(
            telemetry_to_send,
            reading.result * 1000,
            i,
            reading.channel + (10 * (sensor.pin_num/10)));
        }
        else{
          Serial.println(sensor.interface_type_number);
		    	Serial.println("Error. Sensor Interface number is not valid");
	    	}
	    	i++;
	    }
      uint32_t bang_bang_status = do_bang_bang_ox | (do_bang_bang_fuel << 1) | (hot_fireX << 2);
      write_to_telemetry_array(telemetry_to_send,bang_bang_status,i,99); 
      //Serial.println(Udp.remoteIP());
      //Serial.printf("Loop Time (pre-UDP): %d ms\n", millis() - loop_start_time);

      if (Udp.remoteIP()){
  	    Udp.beginPacket(Udp.remoteIP(), 8888);
        Udp.write(telemetry_to_send.data(), telemetry_to_send.size());
  	    Udp.endPacket();
      }
      telemetry_to_send.clear();
      
      //do bang-bang control
      if (moteID == BANG_BANG_BOX_NUM)
        bang_bang();

      //Serial.println(millis());
      //Serial.println(cold_fireX_time);
  
      if (do_fireX && hot_fireX && millis() >= hot_fireX_time){
        Serial.println("HOT FAIL!!");
        hot_fail();
      }
      if (do_fireX && !hot_fireX && millis() >= cold_fireX_time){
        Serial.println("COLD FAIL!!");
        cold_fail();        
      }
      
      delay(loop_delay_ms);
      ticks += 1;
	}
}