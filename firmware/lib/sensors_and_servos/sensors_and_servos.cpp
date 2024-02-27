#include "sensors_and_servos.h"
#include <SparkFun_ADS122C04_ADC_Arduino_Library.h>
#include <Wire.h>
#include "Servo.h"

#include <PWMServo.h>

IntervalTimer PWMServo_Timer;

#define servo_angle 45

/* Flowmeter Board Configuration, 74LS393 */

//See page 2 for truthtable;
//https://www.ti.com/lit/ds/symlink/sn54ls393-sp.pdf?ts=1631127405847&ref_url=https%253A%252F%252Fwww.google.com%252F
//C1-p1 = pin 38 = Q0 = QA  LOWEST ORDER
//C1-p2 = pin 37 = Q1 = QB
//C1-p3 = pin 36 = Q2 = QC
//C1-p4 = pin 35 = Q3 = QD  HIGHEST ORDER
//C1-reset = pin 28
#define FLOWMETER_BIT_THREE 35
#define FLOWMETER_BIT_TWO	36
#define FLOWMETER_BIT_ONE	37
#define FLOWMETER_BIT_ZERO	38
#define FLOWMETER_CLEAR_PIN 28

void test_blink()
{
	digitalWrite(13, HIGH);
	delay(1000);
	digitalWrite(13, LOW);
	delay(1000);
}

void analog_write(int pin_number, int arguement)
/* pinMode() must be setup either through here, or through a configuration block in setup(). */
{
  	
  if (!arguement)
  {
    analogWrite(pin_number, -servo_angle);
  }
  else if(arguement)
  {
    analogWrite(pin_number, servo_angle);
  }
  else
  {
    ;
  }
	
}

void digital_write(int pin_number, bool arguement){
	pinMode(pin_number, OUTPUT);
	if (arguement){
		digitalWrite(pin_number, HIGH);
	} else {
		digitalWrite(pin_number, LOW);
	}
}

void servo_write(PWMServo servo, int pin_number, int arguement)
/* PWM Servo. */
{	
	Serial.println("Turning a servo (now with sane pulse-width v2)!");
	servo.attach(pin_number,3000 - 2150,3000 - 899);
	servo.write(arguement);
}

int teensy_analog_read(int pin_number, int arguement)
/* pinMode() must be setup either through here, or through a configuration block in setup(). */
{
	pinMode(pin_number, INPUT);
	int analog_output = analogRead(pin_number);
	return analog_output;
}

/* For the ADC chip, the initial parameters need to first be adjusted for either 1 wire operation or 2 wire operation. These are based on a structure defined in the ADC's *.h file. Seen here:
*
* // struct to hold the initialisation parameters  (https://github.com/sparkfun/SparkFun_ADS122C04_ADC_Arduino_Library/blob/master/src/SparkFun_ADS122C04_ADC_Arduino_Library.h)
	  typedef struct{
	  uint8_t inputMux;
	  uint8_t gainLevel;
	  uint8_t pgaBypass;
	  uint8_t dataRate;
	  uint8_t opMode;
	  uint8_t convMode;
	  uint8_t selectVref;
	  uint8_t tempSensorEn;
	  uint8_t dataCounterEn;
	  uint8_t dataCRCen;
	  uint8_t burnOutEn;
	  uint8_t idacCurrent;
	  uint8_t routeIDAC1;
	  uint8_t routeIDAC2;
	} ADS122C04_initParam;

There are 4 8-bit configuration registers. On a RESET command, all registers are set to 0.

See Chapter 8.6, Register Map, for more: https://cdn.sparkfun.com/assets/7/4/e/1/4/ads122c04_datasheet.pdf

I2C address is configured physically on each ADC module, referenced chapter "8.5.1.1 I2C Address" here: https://cdn.sparkfun.com/assets/7/4/e/1/4/ads122c04_datasheet.pdf#page=47&zoom=100,0,705

*/

//conversion function
//This is only for saving board sapce. Do not use unless i2c_adc_2_wire doesn't work for some reason
uint32_t i2c_adc_1_wire(SFE_ADS122C04* ADC, int i2c_address, int input_channel)
//https://www.digikey.com/en/maker/projects/qwiic-12-bit-adc-hookup-guide/6b187358d1dc45f6918808d17af94326
//Set default values, then apply masks and multiplexer for single ended operation.
//i2c_address is a binary value, e.g. 0b1000000, 0b1000001, ...
//PGA := Programmable gain amplifier
{
	uint32_t pre_adc_time = millis();
	//Active low. Disables PGA_BYPASS, table 19 of datasheet
	/*			Configure input channel. Table 19 of datasheet
								 1000 : AINP = AIN0, AINN = AVSS
								 1001 : AINP = AIN1, AINN = AVSS
								 1010 : AINP = AIN2, AINN = AVSS
								 1011 : AINP = AIN3, AINN = AVSS
								Input Multiplexer Configuration
									//Differential inputs
								#define ADS122C04_MUX_AIN0_AIN1     0x0
								#define ADS122C04_MUX_AIN0_AIN2     0x1
								#define ADS122C04_MUX_AIN0_AIN3     0x2
								#define ADS122C04_MUX_AIN1_AIN0     0x3
								#define ADS122C04_MUX_AIN1_AIN2     0x4
								#define ADS122C04_MUX_AIN1_AIN3     0x5
								#define ADS122C04_MUX_AIN2_AIN3     0x6
								#define ADS122C04_MUX_AIN3_AIN2     0x7
									//Single ended
								#define ADS122C04_MUX_AIN0_AVSS     0x8
								#define ADS122C04_MUX_AIN1_AVSS     0x9
								#define ADS122C04_MUX_AIN2_AVSS     0xa
								#define ADS122C04_MUX_AIN3_AVSS     0xb
								#define ADS122C04_MUX_REFPmREFN     0xc
								#define ADS122C04_MUX_AVDDmAVSS     0xd
								#define ADS122C04_MUX_SHORTED       0xe
	*/
	ADC->setGain(ADS122C04_GAIN_1);
	ADC->enablePGA(ADS122C04_PGA_DISABLED);	

	if (input_channel == 0) { ADC->setInputMultiplexer(ADS122C04_MUX_AIN3_AVSS); }
	else if (input_channel == 1) { ADC->setInputMultiplexer(ADS122C04_MUX_AIN2_AVSS); }
	else if (input_channel == 2) { ADC->setInputMultiplexer(ADS122C04_MUX_AIN1_AVSS); }
	else if (input_channel == 3) { ADC->setInputMultiplexer(ADS122C04_MUX_AIN0_AVSS); }
	else return -1;
	
	ADC->start(); // Start the conversion
  	unsigned long start_time = millis(); // Record the start time so we can timeout
  	Serial.printf("Multiplex ADC Time: %d ms\n", millis() - pre_adc_time);


	// Wait for DRDY to go valid (by reading Config Register 2)
	// (You could read the DRDY pin instead, especially if you are using continuous conversion mode.)
	
	

	boolean drdy = ADC->checkDataReady();; // DRDY (1 == new data is ready)
	while((drdy == false) && (millis() < (start_time + ADS122C04_CONVERSION_TIMEOUT)))
	{
		delayMicroseconds(550); // Don't pound the I2C bus too hard
		drdy = ADC->checkDataReady();// Read DRDY from Config Register 2
	}
	// Check if we timed out
	if (drdy == false)
	{
		Serial.println(F("checkDataReady timed out"));
		return -1;
	}

	// Read the raw (signed) ADC data
	// The ADC data is returned in the least-significant 24-bits
	
	//int32_t raw_ADC_voltage = ADC->readRawVoltage();
	//uint32_t raw_ADC_data = raw_ADC_voltage + 2147483648; //offset by 2^31 to prevent underflow
	
	uint32_t raw_ADC_data = ADC->readADC();

	raw_voltage_union raw_v;
	raw_v.UINT32 = raw_ADC_data;
	if ((raw_v.UINT32 & 0x00800000) == 0x00800000)
    	raw_v.UINT32 |= 0xFF000000;
  	return (uint32_t)(raw_v.INT32 + 2147483648);
}

uint32_t i2c_adc_2_wire(SFE_ADS122C04 *ADC, int i2c_address, int input_channel, int pga_gain_code)
//i2c_address is a binary value, e.g. 0b1000000, 0b1000001, ...
{	
	if (input_channel == 1) { ADC->setInputMultiplexer(ADS122C04_MUX_AIN1_AIN0); }
	else if (input_channel == 0) { ADC->setInputMultiplexer(ADS122C04_MUX_AIN3_AIN2); }
	else return -1;

	if (pga_gain_code == 0)
		ADC->enablePGA(ADS122C04_PGA_DISABLED);
	else {
		ADC->enablePGA(ADS122C04_PGA_ENABLED);
		ADC->setGain(pga_gain_code);
	}

	ADC->start(); // Start the conversion
  	unsigned long start_time = millis(); // Record the start time so we can timeout
	// Wait for DRDY to go valid (by reading Config Register 2)
	// (You could read the DRDY pin instead, especially if you are using continuous conversion mode.)
	boolean drdy = ADC->checkDataReady();; // DRDY (1 == new data is ready)
	while((drdy == false) && (millis() < (start_time + ADS122C04_CONVERSION_TIMEOUT)))
	{
		delayMicroseconds(550); // Don't pound the I2C bus too hard
		drdy = ADC->checkDataReady();// Read DRDY from Config Register 2
	}

	// Check if we timed out
	if (drdy == false)
	{
		Serial.println(F("checkDataReady timed out"));
		return -1;
	}

	// Read the raw (signed) ADC data
	// The ADC data is returned in the least-significant 24-bits
	
	uint32_t raw_ADC_data = ADC->readADC();

	raw_voltage_union raw_v;
	raw_v.UINT32 = raw_ADC_data;
	if ((raw_v.UINT32 & 0x00800000) == 0x00800000)
    	raw_v.UINT32 |= 0xFF000000;
  	return (uint32_t)(raw_v.INT32 + 2147483648);
}

uint8_t flowmeter_read_wrapper()
{
	/* Possible wrapper for flowmeter_read function to first perform digitalRead on flowmeter pins, assuming they've alread been setup
		Some logic behind nesting functions on embedded systems:
		https://scienceprog.com/function-calls-and-stacking-of-in-embedded-systems/
	*/
	uint8_t current_bit_three, current_bit_two, current_bit_one, current_bit_zero, return_val;

	/* Reading current flowmeter pins.
	See comment #3 for speed tests on digitalRead vs digitalReadFast:
	https://forum.pjrc.com/threads/54363-Teensy-3-6-speed-of-DigitalReadFast
	See comment #3 for reasoning ala Paul (father of Teensy) on using digital____Fast instead of native code:
	https://forum.pjrc.com/threads/23431-Teensy-3-using-IO-pins */

	current_bit_three = digitalReadFast(FLOWMETER_BIT_THREE);
	current_bit_two = digitalReadFast(FLOWMETER_BIT_TWO);
	current_bit_one = digitalReadFast(FLOWMETER_BIT_ONE);
	current_bit_zero = digitalReadFast(FLOWMETER_BIT_ZERO);

	return_val = flowmeter_read(current_bit_three, current_bit_two, current_bit_one, current_bit_zero, 0);
	return return_val;
}

uint8_t flowmeter_read(uint8_t bit_three, uint8_t bit_two, uint8_t bit_one, uint8_t bit_zero, uint8_t reset)
{
	//Reads a 4 bit counter, through 4 digitalReads. 1 reset pin. 
	//See schematic.
	//Masks bits for return value. Input parameters are weird, with the msot significant bit entered first. 
	//   bit_three -> 0 0 0 0 <- bit_one
	uint8_t return_value = 0b0000;

	//I'm not sure if CLEAR is active low or high, so that needs to be tested. FLOWMETER_CLEAR_PIN also needs to be setup through 
	if (reset)
	{
		digitalWrite(FLOWMETER_CLEAR_PIN, HIGH);
		delay(250); //Delay to wait for reset. TODO: See datasheet for more specific timing requirement
		digitalWrite(FLOWMETER_CLEAR_PIN, LOW);
	}

	if (bit_zero) return_value |= 0b0001;
	if (bit_one) return_value |= 0b0010;
	if (bit_two) return_value |= 0b0100;
	if (bit_three) return_value |= 0b1000;

	return return_value;
}

float i2c_adc_internal_temp(SFE_ADS122C04 *ADC, int i2c_address)
{
	//ADC.reset();
	float return_val = ADC->readInternalTemperature(ADS122C04_DATA_RATE_1000SPS);
	return return_val;
}

uint32_t AD7193_driver(AD7193_driver_arg_t args){
    //Basic init stuff -- figure out which SPI bus we're using, then get and set the right pins accordingly...
    uint8_t CS_pin = (args.spi_bus == &SPI)? 10 : 0;
    uint8_t rdy_pin = (args.spi_bus == &SPI)? 12 : 1;
    pinMode(CS_pin, OUTPUT);
    digitalWrite(CS_pin, LOW);
    //ADC enters a low power mode after making a conversion, so we have to wait for it to fully power up before communicating with it to avoid problems...

    //TODO WARNING this statement is not thread safe. Make it so when integrating with MINOS
    args.spi_bus->transfer(args.comm_bits);
    
    uint8_t reg_id = args.comm_bits & 0b00111000;
    if(args.comm_bits & AD7193_REG_READ){
        //Reading data from one of the ADC's registers...
        //Readable registers in the AD7193 have one of two sizes: 8-bit, and 24-bit. The 8-bit registers are STATUS, ID, and GPOCON, with all others being 24-bit...
        if(reg_id == AD7193_STATUS_REG || reg_id == AD7193_ID_REG || reg_id == AD7193_GPOCON_REG)
            return args.spi_bus->transfer(0);
        else{
            //Read operations from the data register trigger a fresh conversion in the ADC, so we have to wait for the result to settle before reading...
            //The ADC signals that it's ready to output a reading by bringing its D_OUT pin low (without being triggered by the clock), so we wait for this to happen before proceeding...
            if(reg_id == AD7193_DATA_REG){
                while(1){
                    if(digitalRead(rdy_pin) == LOW)
                        break;
                    delay(1);
					Serial.println("Waiting for data ready.");
                }
            }
            uint32_t sensor_return = 0;
            //Bits are delivered to us going from MSB to LSB...
            //Include logic here to account for whether or not the status register bits are being appended!!!!
            sensor_return |= args.spi_bus->transfer(0) << 24;
            sensor_return |= args.spi_bus->transfer(0) << 16;
            sensor_return |= args.spi_bus->transfer(0) << 8;
            sensor_return |= args.spi_bus->transfer(0);
            return sensor_return;
        }
        //End of READ if-block...
    }
    else{
        //Writing data to one of the ADC's registers...
        //Only one of the AD7193's writeable registers has 8-bit size -- the rest are 24-bit...
        if(reg_id == AD7193_GPOCON_REG)
            args.spi_bus->transfer((uint8_t)args.write_payload);
        else{
            //We transfer the bits going from MSB to LSB...
            args.spi_bus->transfer((uint8_t)(args.write_payload >> 16));
            args.spi_bus->transfer((uint8_t)(args.write_payload >> 8));
            args.spi_bus->transfer((uint8_t)args.write_payload);
        }
        return 0;
        //End of WRITE else-block
    }
    //Deselect device to avoid spurious writes...
    digitalWrite(CS_pin, HIGH);
}

double AD7193_codeToVolts(uint32_t code, uint16_t currentGainSetting, bool unipolar){
    //These formulas both appear on page 33 of the AD7193 data sheet!!!
    if(unipolar)        //Evaluates to 'true' if ADC is in unipolar mode! Following is the formula for the unipolar case...
        return ((double)(code * VREF)) / ((double)(AD7193_CODE_EXP_TERM));

    //If the above conditional statement fails, then the ADC is in bipolar mode! Following is the formula for the bipolar case...
    return ( ( (double)code / ((double)AD7193_CODE_EXP_TERM / 2) ) - 1 ) / ( (double)1.0 / (double)VREF );
}

void configure_AD7193(AD7193_arg_t args) {
	Serial.println("START CONFIG");

	AD7193_reading_t new_reading;
	SPI.begin();
	SPI1.begin();

	uint16_t gain_bits;
    switch(args.pga_gain){
        case 1:     gain_bits = 0x0;    break;
        case 8:     gain_bits = 0x03;   break;
        case 16:    gain_bits = 0x04;   break;
        case 32:    gain_bits = 0x05;   break;
        case 64:    gain_bits = 0x06;   break;
        case 128:   gain_bits = 0x07;   break;
        default:    gain_bits = 0x0;
    }

    Serial.println(gain_bits);

    uint16_t channel_bits = 0x0;
    channel_bits |= args.channel_bits;

    //differential bit is flipped, this is because it is a "psuedo" bit in the datasheet. I.e, if the bit is set, take differential against AINCOM instead of an input
    uint32_t config_write_payload = 0x0 | (!args.differential << AD7193_DIFFERENTIAL_BIT) | channel_bits | (gain_bits) ;
    Serial.println(config_write_payload & 0b111);

    AD7193_driver_arg_t driver_args;
    driver_args.comm_bits = AD7193_REG_WRITE | AD7193_CONFIG_REG;
    driver_args.write_payload = config_write_payload;

    switch (args.spi_num) {
        case 0: driver_args.spi_bus = &SPI; break;
        case 1: driver_args.spi_bus = &SPI1; break;
        default: driver_args.spi_bus = &SPI;
    }
	
	Serial.println("CALL DRIVER 1");
    AD7193_driver(driver_args);

    uint32_t mode_reg_payload = 0x080060 | (1 << 20);
    driver_args.comm_bits = AD7193_REG_WRITE | AD7193_MODE_REG;
    driver_args.write_payload = mode_reg_payload;
	Serial.println("CALL DRIVER 2");
    AD7193_driver(driver_args);

	Serial.println("DONE WITH ADC CONFIG");
}

AD7193_reading_t read_AD7193(AD7193_arg_t args) {
	AD7193_reading_t new_reading;

	uint16_t gain_bits;
    switch(args.pga_gain){
        case 1:     gain_bits = 0x0;    break;
        case 8:     gain_bits = 0x03;   break;
        case 16:    gain_bits = 0x04;   break;
        case 32:    gain_bits = 0x05;   break;
        case 64:    gain_bits = 0x06;   break;
        case 128:   gain_bits = 0x07;   break;
        default:    gain_bits = 0x0;
    }

    AD7193_driver_arg_t new_driver_args;
    new_driver_args.comm_bits = AD7193_REG_READ | AD7193_DATA_REG;
	
	switch (args.spi_num) {
        case 0: new_driver_args.spi_bus = &SPI; break;
        case 1: new_driver_args.spi_bus = &SPI1; break;
        default: new_driver_args.spi_bus = &SPI;
    }

    uint32_t result = AD7193_driver(new_driver_args);

    new_reading.channel = result & 0x7F;

    double units;
    if (!args.internal_temp) {
        new_reading.result = AD7193_codeToVolts(result >> 8, gain_bits, false);
    } else {
        new_reading.result = (result - 0x800000)/2815.0 - 273;
    }

	return new_reading;
}