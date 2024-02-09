// Network constants.
#define PORT 8888

#define MAC1 {0x36, 0x47, 0xA4, 0x6B, 0x46, 0x13}
#define MAC2 {0x28, 0x64, 0x53, 0xE8, 0xAE, 0xF8}
#define MAC3 {0x9C, 0xAA, 0x98, 0xE1, 0x26, 0x25}
#define MAC4 {0x7D, 0x99, 0x8F, 0x1B, 0xF0, 0x8A}

// Sensor constants
typedef enum {
    TEENSY_ADC = 1,
    I2C_ADC_1CH,
    I2C_ADC_2CH,
    FLOWMETER,
    I2C_ADC_2CH_MIN_GAIN = 7,
    I2C_ADC_2CH_MAX_GAIN = 13,
    INTERNAL_TEMP,
    SPI_ADC_1CH,
    SPI_ADC_2CH,
    SPI_ADC_2CH_MIN_GAIN,
    SPI_ADC_2CH_MAX_GAIN = 23,
} sensor_interface_num_t;

#define SENSOR_CLEAR_CODE 44

// Actuator constants
typedef enum {
    PWM_SERVO = 5,
    BINARY_LOAD_SWITCH,
    BANG_BANG_CONTROL = 41,
    AUTO_FIREX_CONTROL,
    HEARTBEAT
} actuator_interface_num_t;