// sensors_and_servos.h

#ifndef _SENSORS_AND_SERVOS_h
#define _SENSORS_AND_SERVOS_h

#if defined(ARDUINO) && ARDUINO >= 100
	#include  <Arduino.h>
	#include <PWMServo.h>
  	#include <Servo.h>
	#include <SparkFun_ADS122C04_ADC_Arduino_Library.h>
	#include <Wire.h>
	#include <SPI.h>
#else
	#include "WProgram.h"
#endif

void analog_write(int pin_number, int arguement);
void digital_write(int pin_number, bool arguement);
void servo_write(PWMServo Servo, int pin_number, int arguement);
void servo_write_wrapper(Servo Servo, int pin_number, int arguement, int run_time);
int teensy_analog_read(int pin_number, int arguement);
uint32_t i2c_adc_1_wire(SFE_ADS122C04 *ADC, int i2c_address, int input_channel);
uint32_t i2c_adc_2_wire(SFE_ADS122C04 *ADC, int i2c_address, int input_channel, int pga_gain_code);
uint8_t flowmeter_read_wrapper();
uint8_t flowmeter_read(uint8_t bit_three, uint8_t bit_two, uint8_t bit_one, uint8_t bit_zero, uint8_t reset);
float i2c_adc_internal_temp(SFE_ADS122C04 *ADC, int i2c_address);
void test_blink();



//Macros relevant to the Communications register... (the first byte transferred to the AD7193 in a transaction will always be written to the Comm register, so it has no unique address)
//Bits 0, 6, and 7 must always be empty (0). Bit 1 = r/w ; bits 2-4 = register address ; bit 5 = enable continuous read (has an effect for data reg reads only)
#define AD7193_REG_READ 0b01000000            //Signals a read operation
#define AD7193_REG_WRITE 0b00000000           //Signals a write operation
#define AD7193_STATUS_REG 0b00000000        //8-bit reg (r)
#define AD7193_MODE_REG 0b00001000          //24-bit reg (r/w)  
#define AD7193_CONFIG_REG 0b00010000        //24-bit reg (r/w)
#define AD7193_DATA_REG 0b00011000          //24-bit reg (r)
#define AD7193_ID_REG 0b00100000            //8-bit reg (r)
#define AD7193_GPOCON_REG 0b00101000        //8-bit reg (r/w)
#define AD7193_OFFSET_REG 0b00110000        //24-bit reg (r/w)
#define AD7193_FULLSCALE_REG 0b00111000     //24-bit reg (r/w)

#define AD7193_CHANNEL_BIT 8
#define AD7193_DIFFERENTIAL_BIT 18
#define AD7193_PGA_BIT 0
#define AD7183 POLARITY_BIT 3
#define AD7193_CHANNEL_SHIFT 0x00000100

//Have to include some global variables here that affect the conversion from output code to volts for the AD7193 --
//change these in the AD7193 functions or hardcode them to something if they're never going to change!!!

//This info appears on sheet 3 of the MoteV5 schematic -- it appears as REFIN1(+)!!
#define VREF 5
#define AD7193_CODE_EXP_TERM 16777216   //This is 2^24

#define TEENSY_INTERNAL_ADC_PIN 14

typedef struct {
    uint8_t comm_bits;
    uint32_t write_payload;
    SPIClass* spi_bus;      //To fill this field, please use either "&SPI" (for AD7193 1) or "&SPI1" (for AD7193 2)!!!
} AD7193_driver_arg_t;

typedef struct {
    bool internal_temp; //if this bool is TRUE, all other parameters will be ignored

    bool differential;
    uint8_t spi_num; //should be 0 or 1
    uint32_t channel_bits;
    uint16_t pga_gain;
} AD7193_arg_t;

typedef struct
{
    uint8_t channel;
    double result;
} AD7193_reading_t;

AD7193_reading_t read_AD7193(AD7193_arg_t args);
void configure_AD7193(AD7193_arg_t args);

#endif
