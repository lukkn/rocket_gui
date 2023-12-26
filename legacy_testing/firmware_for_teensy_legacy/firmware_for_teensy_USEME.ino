/*
 Name:		firmware_for_teensy_USEME.ino
 Created:	6/28/2021 10:49:21 AM
 Author:	bmk
*/
#include "sensors_and_servos.h"

#define debug 1;
#define test_i2c_address 0b1000000


PWMServo my_PWMServo;
Servo my_Servo;
SFE_ADS122C04 my_ADC;

// the setup function runs once when you press reset or power the board
void setup() {
	/* Serial for debugging */
	Serial.begin(9600);
/*
	while (!Serial) {
		; // wait for serial port to connect. Needed for native USB
	}
*/
	Serial.println("Hello World from Serial!");
	pinMode(13, OUTPUT);		//Power light. 
  digitalWrite(13, HIGH);
  //pinMode(21, OUTPUT);

	Serial.println("Starting wire");
	Wire.begin();
  
	Serial.println("Starting ADC");
	my_ADC.begin(0x40, Wire);

  my_ADC.setInputMultiplexer(ADS122C04_MUX_AIN1_AIN0); // Route AIN1 and AIN0 to AINP and AINN
  my_ADC.setGain(ADS122C04_GAIN_1); // Set the gain to 1
  my_ADC.enablePGA(ADS122C04_PGA_DISABLED); // Disable the Programmable Gain Amplifier
  my_ADC.setDataRate(ADS122C04_DATA_RATE_20SPS); // Set the data rate (samples per second) to 20
  my_ADC.setOperatingMode(ADS122C04_OP_MODE_NORMAL); // Disable turbo mode
  my_ADC.setConversionMode(ADS122C04_CONVERSION_MODE_SINGLE_SHOT); // Use single shot mode
  my_ADC.setVoltageReference(ADS122C04_VREF_INTERNAL); // Use the internal 2.048V reference
  my_ADC.enableInternalTempSensor(ADS122C04_TEMP_SENSOR_OFF); // Disable the temperature sensor
  my_ADC.setDataCounter(ADS122C04_DCNT_DISABLE); // Disable the data counter (Note: the library does not currently support the data count)
  my_ADC.setDataIntegrityCheck(ADS122C04_CRC_DISABLED); // Disable CRC checking (Note: the library does not currently support data integrity checking)
  my_ADC.setBurnOutCurrent(ADS122C04_BURN_OUT_CURRENT_OFF); // Disable the burn-out current
  my_ADC.setIDACcurrent(ADS122C04_IDAC_CURRENT_OFF); // Disable the IDAC current
  my_ADC.setIDAC1mux(ADS122C04_IDAC1_DISABLED); // Disable IDAC1
  my_ADC.setIDAC2mux(ADS122C04_IDAC2_DISABLED); // Disable IDAC2

  my_ADC.enableDebugging(Serial); //Enable debug messages on Serial
  my_ADC.printADS122C04config(); //Print the configuration
  my_ADC.disableDebugging(); //Enable debug messages on Serial
  
  //Testing Servo
  //my_PWMServo.attach(21);
  //my_Servo.attach(23);
}

// the loop function runs over and over again until power down or reset
void loop() {
	//test_blink();

	//Testing Servos
	//servo_write(my_Servo, 9, 45);

	//Testing ADC wire:
 
	//Serial.print("ADC internal temp: ");
	//Serial.println(i2c_adc_internal_temp(my_ADC, 0x40));
  //Serial.print("ADC 1ch Value: ");
	//Serial.println(i2c_adc_1_wire(my_ADC, test_i2c_address, 1));
  Serial.print("ADC 2ch Value: ");  
	Serial.println(i2c_adc_2_wire(my_ADC, test_i2c_address));

  /*
	//Testing Flowmeter: 
	uint8_t flowmeter_value = flowmeter_read(0,1,1,0,0);

	Serial.print("Flowmeter value (0 - 15): ");
	Serial.println(flowmeter_value);
  delay(1000);
  */
}
