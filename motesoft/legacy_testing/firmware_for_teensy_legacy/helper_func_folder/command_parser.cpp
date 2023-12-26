//will be used in the teensy
#include <iostream>
#include <cstring>
#include <vector>

//WARNING TESTED BUT NOT TESTED ENOUGH
using namespace std;

//In arduino: int and float are four bytes
//strictly use uint8_t not char, int, unsigned char
//if you want to use vectors inside arduino call for stl library for c++ in arduino
//arduino ide uses c++11 and cpp will be also c++11

/* RETRIEVING AND PARSING COMMANDS */
//retrieve pin number from command packet
uint8_t get_pin_num (uint8_t command_byte_array[])
{
    uint8_t first_byte = command_byte_array[0];
    uint8_t pin = (uint8_t) first_byte;

    return pin;
}

//retrieve bit to write or not for actuators
uint8_t get_actuator_write (uint8_t command_byte_array[]){
    uint8_t second_byte = command_byte_array[1];
    uint8_t isWrite = (uint8_t)((second_byte & 0x80)>>7); //msb
    return isWrite;
}

//retrieve state for writing for actuators
uint8_t get_actuator_state (uint8_t command_byte_array[]){
    uint8_t second_byte = command_byte_array[1];
    uint8_t state = (uint8_t)((second_byte & 0x40)>>6); //second msb bit

    return state;
}

//retrieve interface number from last byte
uint8_t get_interface_num (uint8_t command_byte_array[]){
    uint8_t second_byte = command_byte_array[1];
    uint8_t interface_num = ((second_byte & 0x3F)); //last 6 bits

    return interface_num;
}

/* SENDING DATA PACKETS */
//necessary everytime you finish sending the array
inline void dealloc_packet_array (char * ptr){
    delete ptr;
}

//print the vector as bytes
template<typename B> 
void print_byte_vector(vector<B> input_vect){
    uint8_t * print_array = reinterpret_cast<uint8_t *>(&input_vect[0]);

    for (std::size_t i = 0; i != sizeof(B) * input_vect.size(); ++i)
    {
        printf("The byte #%zu is 0x%02X\n", i, print_array[i]);
    }
}

//printing out the packet to check
void print_packet_array(int num_sensors, uint8_t* packet){

    for (int j = 0; j < num_sensors; j++){
        // printf("Pin: %u \n", *((uint8_t *)(packet+5*j+0)));

        // printf("Data Val: %f \n", *((float *)(packet+5*j+1)));
        printf("Pin: %x Data Val: %f \n", *((uint8_t *)(packet+5*j+0)), *((float *)(packet+5*j+1)));
    }
}

//build the packet, will initialize array in heap to avoid local scope
//must be deallocated outside function once sending packets is finished.
//maybe make as inline?
//note reinterpret is done during runtime, will not be stored but reinterpreted
uint8_t * build_data_packet (vector <uint8_t> pin_num_vect, vector <float> float_measure_vect){
    if (pin_num_vect.size() != float_measure_vect.size()){
        return 0;
    }

    uint8_t * pin_ptr = reinterpret_cast<uint8_t *>(&pin_num_vect[0]);
    uint8_t * data_ptr = reinterpret_cast<uint8_t *>(&float_measure_vect[0]);

    uint8_t num_sensor = pin_num_vect.size();
    uint8_t num_bytes = num_sensor * 5;
    uint8_t * packet = new uint8_t [num_bytes];


    for (uint8_t i = 0 ; i < num_sensor; i++){
        uint8_t pkt_idx = i * 5;
        uint8_t float_idx = i * 4;
        
        packet[pkt_idx + 0] = pin_ptr [i];
        packet[pkt_idx + 1] = data_ptr[float_idx + 0];
        packet[pkt_idx + 2] = data_ptr[float_idx + 1];
        packet[pkt_idx + 3] = data_ptr[float_idx + 2];
        packet[pkt_idx + 4] = data_ptr[float_idx + 3];


    }

    return packet;
}

//this is to test
int main(){

    uint8_t command_byte_array []= {0xFF, 0xFF}; //pinnum = 255, write = 1, state = 1, interface= 2^6 -1 = 63 
    cout << "Pin_num " << (int) get_pin_num (command_byte_array) << endl; 
    cout << "Act_Wr " << (int) get_actuator_write (command_byte_array) << endl;
    cout << "Act_State " << (int) get_actuator_state (command_byte_array) << endl; 
    cout << "Interface_num " << (int) get_interface_num (command_byte_array) << endl; 

    vector <uint8_t> pin_num_vect = {1,2,3,4,5,6,7,8,9,10,11};
    vector <float> data_measure_vect = {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0};
    
    uint8_t* pkt = build_data_packet (pin_num_vect, data_measure_vect);
    print_packet_array (pin_num_vect.size(), pkt);
}

//things for benL, make a new file called test.cpp, get rid of main function, create all tests cases
//crete a makefile
//also do encoding for sending config file