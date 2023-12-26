#include "Arduino.h"
#include <SPI.h>

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
} AD7193_arg_t;

typedef struct {
    //Can add more config fields to this if necessary.
    //The channel settings are 10 bits occupying the range [17:8] within the config register, so any valid value for channel_settings must use no more than the 10 LSBs of the word!
    //Also, it will need to be left shifted by 8 bits before it can be safely inserted into a config write payload.
    bool internal_temp; //if this bool is TRUE, all other parameters will be ignored

    bool differential;
    uint16_t spi_num; //should be 0 or 1
    uint16_t channel;
    uint16_t pga_gain;
} AD7193_wrapper_arg_t;

int AD7193_driver(void* args){
    //NOT DONE! WIP...
    //If any problems occur during testing, they are more than likely going to be related to SPI/conversion timing!!!
    AD7193_arg_t* s_args = (AD7193_arg_t*) args;
    //Basic init stuff -- figure out which SPI bus we're using, then get and set the right pins accordingly...
    uint8_t CS_pin = (s_args->spi_bus == &SPI)? 10 : 0;
    uint8_t rdy_pin = (s_args->spi_bus == &SPI)? 12 : 1;
    pinMode(CS_pin, OUTPUT);
    digitalWrite(CS_pin, LOW);
    //ADC enters a low power mode after making a conversion, so we have to wait for it to fully power up before communicating with it to avoid problems...

    //TODO WARNING this statement is not thread safe. Make it so when integrating with MINOS
    delay(1);

    s_args->spi_bus->begin();
    s_args->spi_bus->transfer(s_args->comm_bits);
    
    uint8_t reg_id = s_args->comm_bits & 0b00111000;
    if(s_args->comm_bits & AD7193_REG_READ){
        //Reading data from one of the ADC's registers...
        //Readable registers in the AD7193 have one of two sizes: 8-bit, and 24-bit. The 8-bit registers are STATUS, ID, and GPOCON, with all others being 24-bit...
        if(reg_id == AD7193_STATUS_REG || reg_id == AD7193_ID_REG || reg_id == AD7193_GPOCON_REG)
            return s_args->spi_bus->transfer(0);
        else{
            //Read operations from the data register trigger a fresh conversion in the ADC, so we have to wait for the result to settle before reading...
            //The ADC signals that it's ready to output a reading by bringing its D_OUT pin low (without being triggered by the clock), so we wait for this to happen before proceeding...
            if(reg_id == AD7193_DATA_REG){
                while(1){
                    if(digitalRead(rdy_pin) == LOW)
                        break;
                    delay(1);
                }
            }
            uint32_t sensor_return = 0;
            //Bits are delivered to us going from MSB to LSB...
            //Include logic here to account for whether or not the status register bits are being appended!!!!
            sensor_return |= s_args->spi_bus->transfer(0) << 16;
            sensor_return |= s_args->spi_bus->transfer(0) << 8;
            sensor_return |= s_args->spi_bus->transfer(0);
            return sensor_return;
        }
        //End of READ if-block...
    }
    else{
        //Writing data to one of the ADC's registers...
        //Only one of the AD7193's writeable registers has 8-bit size -- the rest are 24-bit...
        if(reg_id == AD7193_GPOCON_REG)
            s_args->spi_bus->transfer((uint8_t)s_args->write_payload);
        else{
            //We transfer the bits going from MSB to LSB...
            s_args->spi_bus->transfer((uint8_t)(s_args->write_payload >> 16));
            s_args->spi_bus->transfer((uint8_t)(s_args->write_payload >> 8));
            s_args->spi_bus->transfer((uint8_t)s_args->write_payload);
        }
        return 0;
        //End of WRITE else-block
    }
    //Deselect device to avoid spurious writes...
    digitalWrite(CS_pin, HIGH);
}

double AD7193_codeToVolts(uint32_t code, uint16_t currentGainSetting, bool unipolar){
    //The following gain codes appear on page 28 of the AD7193 data sheet! (I have no idea what "Reserved" means there or what those codes are for, hopefully it's not anything important >_<!!)
    int gain = 1;
    /*switch(currentGainSetting){
        case 0x00: break;
        case 0x03: gain = 8; break;
        case 0x04: gain = 16; break;
        case 0x05: gain = 32; break;
        case 0x06: gain = 64; break;
        case 0x07: gain = 128; break;
    }*/

    //These formulas both appear on page 33 of the AD7193 data sheet!!!
    if(unipolar)        //Evaluates to 'true' if ADC is in unipolar mode! Following is the formula for the unipolar case...
        return ((double)(code * VREF)) / ((double)(AD7193_CODE_EXP_TERM));

    //If the above conditional statement fails, then the ADC is in bipolar mode! Following is the formula for the bipolar case...
    return ( ( (double)code / ((double)AD7193_CODE_EXP_TERM / 2) ) - 1 ) / ( (double)1.0 / (double)VREF );
}

//Use the following function if configs need to be adjusted before making a read. Otherwise, use the raw driver above.
int AD7193_wrapper(void* args){
    AD7193_wrapper_arg_t* configs = (AD7193_wrapper_arg_t*)args;
    //Form a configuration bit-string...
    
    uint16_t gain_bits;
    switch(configs->pga_gain){
        case 1:     gain_bits = 0x0;    break;
        case 8:     gain_bits = 0x03;   break;
        case 16:    gain_bits = 0x04;   break;
        case 32:    gain_bits = 0x05;   break;
        case 64:    gain_bits = 0x06;   break;
        case 128:   gain_bits = 0x07;   break;
        default:    gain_bits = 0x0;
    }

    Serial.println(gain_bits);

    uint16_t channel_bits;
    if (configs->internal_temp) {
        channel_bits = 8;
    } else {
        channel_bits = (configs->channel - 1);
    }

    //differential bit is flipped, this is because it is a "psuedo" bit in the datasheet. I.e, if the bit is set, take differential against AINCOM instead of an input
    uint32_t config_write_payload = 0x0 | (!configs->differential << AD7193_DIFFERENTIAL_BIT) | (AD7193_CHANNEL_SHIFT << channel_bits) | (gain_bits) ;
    Serial.println(config_write_payload & 0b111);

    AD7193_arg_t driver_args;
    driver_args.comm_bits = AD7193_REG_WRITE | AD7193_CONFIG_REG;
    driver_args.write_payload = config_write_payload;

    switch (configs->spi_num) {
        case 0: driver_args.spi_bus = &SPI; break;
        case 1: driver_args.spi_bus = &SPI1; break;
        default: driver_args.spi_bus = &SPI;
    }
    
    AD7193_driver((void*)&driver_args);
    //Just reuse the old structure to avoid waste. The payload section doesn't need to be changed since the driver ignores it on read operations.
    driver_args.comm_bits = AD7193_REG_READ | AD7193_DATA_REG;

    int result = AD7193_driver((void*)&driver_args);
    Serial.println(result);

    double units;
    if (!configs->internal_temp) {
        units = AD7193_codeToVolts(result, gain_bits, false);
    } else {
        units = (result - 0x800000)/2815.0 - 273;
    }
    
    return units * 1000; //integral number of millivolts
}

void setup() {
    //pinMode(LED_BUILTIN, OUTPUT);    
    Serial.begin(9600);
    delay(100);
    Serial.println("Startup complete");
}

void loop() {
    AD7193_wrapper_arg_t w_args;
    w_args.channel = 2;
    w_args.pga_gain = 16;
    w_args.differential = false;

    w_args.spi_num = 1;
    w_args.internal_temp = false;

    Serial.println("Reading ADC..");

    int mV = AD7193_wrapper(&w_args);

    Serial.println(mV/1000.0);

    delay(1000);
}