#WARNING NOT TESTED

import struct

#no difference in functionality between byte string and byte array but one is immutable
#and other is not

#use byte array versusbyte string

#for testing purposes: sometimes prints char repr from asccivalue, prins the all hex
def print_bytes_hex (byte_object):
    print(''.join(r'\x'+hex(letter)[2:] for letter in byte_object))

# create packet to send the client (needs pin_num and config byte)
def create_command_pkt(pin_num, act_write, act_state, interface_num):

    #create first byte
    first_byte = bytes([pin_num]) #musts only be 0-256 cuz only convert 1 byte
    
    #create the second byte

    if interface_num < 0 or interface_num >= 2**6:
        print("Inteface num must fit in 6 bits (0-63)")
        return -1

    interface_bytes = bytes([interface_num])
    mask_1 = b'\x3f'
    second_byte = bytes([interface_bytes[0] & mask_1[0]]) #clear the 2 msb bits

    if act_state:
        mask_2 = b'\x4f'
        second_byte = bytes([second_byte[0] | mask_2[0]])

    if act_write:
        mask_3 = b'\x8f'
        second_byte = bytes([second_byte[0] | mask_3[0]])
    
    command_pkt = first_byte + second_byte # combines both bytes

    return command_pkt

# interpret the data from packet (instead of making list, just pull it from indexing)
#list of tuples
def read_data_pkt (data_pkt):
    data_measure_list = []

    for idx, byte_val in enumerate(data_pkt[::5]):
        index = 5*idx
        
        pin_num = byte_val
        
        float_byteString = bytes([data_pkt[index+1]]) +bytes([data_pkt[index+2]])+bytes([data_pkt[index+3]])+bytes([data_pkt[index+4]])
        float_val = struct.unpack('f', float_byteString)[0]
        
        data_pair = (pin_num, float_val) #(pin num, float)
        data_measure_list.append(data_pair)
    return data_measure_list

# for testing purposes
# if __name__ == "__main__":

#     pkt = b'\x05\x33\x33\xa3\x40'
#     pkt += b'\x05\x33\x33\xa3\x40'
    
#     create_command_pkt(255, 1, 1, 63)
#     L = read_data_pkt(pkt)

#     print(L)


    

