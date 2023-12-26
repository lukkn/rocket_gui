CORES_PATH = ../cores/teensy4
Libraries_PATH = ../libraries #only used for cleaning. can be rewritten to use LIBRARIES but I don't have time rn
LIBRARIES = NativeEthernet/src FNET/src MODIFIED_PWMServo
CORESRCDIRS  = $(addprefix ../libraries/,$(LIBRARIES))
COREINCS     = $(addprefix -I,$(CORESRCDIRS))
CORE_CC_SRC  = $(foreach dir,$(CORESRCDIRS), $(shell find $(dir) -name "*.c"))
CORE_CXX_SRC = $(foreach dir,$(CORESRCDIRS), $(shell find $(dir) -name "*.cpp"))

# Use these lines for Teensy 4.1
MCU = IMXRT1062
MCU_LD = $(CORES_PATH)/imxrt1062_t41.ld
MCU_DEF = ARDUINO_TEENSY41

# The name of your project (used to name the compiled .hex file)
TARGET = main

# configurable options
OPTIONS = -DF_CPU=600000000 -DUSB_SERIAL -DLAYOUT_US_ENGLISH -DUSING_MAKEFILE -I$(CORES_PATH) $(COREINCS)
#OPTIONS = -DF_CPU=600000000 -DUSB_SERIAL -DLAYOUT_US_ENGLISH -DUSING_MAKEFILE -I$(CORES_PATH)

# options needed by many Arduino libraries to configure for Teensy model
OPTIONS += -D__$(MCU)__ -DARDUINO=10813 -DTEENSYDUINO=154 -D$(MCU_DEF)

# for Cortex M7 with single & double precision FPU
CPUOPTIONS = -mcpu=cortex-m7 -mfloat-abi=hard -mfpu=fpv5-d16 -mthumb

# use this for a smaller, no-float printf
#SPECS = --specs=nano.specs

#************************************************************************
# Location of Teensyduino utilities, Toolchain, and Arduino Libraries.
# To use this makefile without Arduino, copy the resources from these
# locations and edit the pathnames.  The rest of Arduino is not needed.
#************************************************************************

# Those that specify a NO_ARDUINO environment variable will
# be able to use this Makefile with no Arduino dependency.
# Please note that if ARDUINOPATH was set, it will override
# the NO_ARDUINO behaviour.
ifndef NO_ARDUINO
# Path to your arduino installation
ARDUINOPATH ?= ../../../../..
endif

ifdef ARDUINOPATH

# path location for Teensy Loader, teensy_post_compile and teensy_reboot (on Linux)
TOOLSPATH = $(abspath $(ARDUINOPATH)/hardware/tools)

# path location for Arduino libraries (currently not used)
LIBRARYPATH = $(abspath $(ARDUINOPATH)/libraries)

# path location for the arm-none-eabi compiler
COMPILERPATH = $(abspath $(ARDUINOPATH)/hardware/tools/arm/bin)

else
# Default to the normal GNU/Linux compiler path if NO_ARDUINO
# and ARDUINOPATH was not set.
COMPILERPATH ?= /usr/bin

endif
COMPILERPATH = /usr/bin
#************************************************************************
# Settings below this point usually do not need to be edited
#************************************************************************

# CPPFLAGS = compiler options for C and C++
CPPFLAGS = -Wall -g -O2 $(CPUOPTIONS) -MMD $(OPTIONS) -I. -ffunction-sections -fdata-sections

# compiler options for C++ only
CXXFLAGS = -std=gnu++14 -felide-constructors -fno-exceptions -fpermissive -fno-rtti -Wno-error=narrowing

# compiler options for C only
CFLAGS =

# linker options
LDFLAGS = -Os -Wl,--gc-sections,--relax $(SPECS) $(CPUOPTIONS) -T$(MCU_LD)

# additional libraries to link
#LIBS = -larm_cortexM7lfsp_math -lm -lstdc++
LIBS = -lm -lstdc++ #TODO FIXME TODO FIXME TODO FIXME TODO FIXME TODO FIXME


# names for the compiler programs
CC = $(COMPILERPATH)/arm-none-eabi-gcc
CXX = $(COMPILERPATH)/arm-none-eabi-g++
OBJCOPY = $(COMPILERPATH)/arm-none-eabi-objcopy
SIZE = $(COMPILERPATH)/arm-none-eabi-size

# automatically create lists of the sources and objects
# TODO: this does not handle Arduino libraries yet...
#C_FILES := $(wildcard $(CORES_PATH)/*.c) $(shell find $(Libraries_PATH) -name "*.c") $(wildcard *.c)
#CPP_FILES := $(wildcard $(CORES_PATH)/*.cpp) $(shell find $(Libraries_PATH) -name "*.cpp") $(wildcard *.cpp)
#C_FILES := $(filter-out $(CORES_PATH)/main.c, $(C_FILES))
#CPP_FILES := $(filter-out $(CORES_PATH)/main.cpp, $(CPP_FILES))

C_FILES := $(wildcard *.c) $(filter-out $(CORES_PATH)/main.c, $(wildcard $(CORES_PATH)/*.c)) $(CORE_CC_SRC)
CPP_FILES := $(wildcard *.cpp) $(filter-out $(CORES_PATH)/main.cpp, $(wildcard $(CORES_PATH)/*.cpp)) $(CORE_CXX_SRC)

#NOTE: the FNET library has both c and cpp files with same name, so they (normally) would produce the same object file (one being overwritten), so the following keeps them from overwriting eachother
OBJS := $(C_FILES:.c=.c.o) $(CPP_FILES:.cpp=.cpp.o)


# the actual makefile rules (all .o files built by GNU make's default implicit rules)

%.c.o : %.c
	$(CC) -c $(CFLAGS) $(CPPFLAGS) $< -o $@
%.cpp.o : %.cpp
	$(CXX) -c $(CPPFLAGS) $(CXXFLAGS) $< -o $@

all: $(TARGET).hex

$(TARGET).elf: $(OBJS) $(MCU_LD)
	$(CC) $(LDFLAGS) -o $@ $(OBJS) $(LIBS)

%.hex: %.elf
	$(SIZE) $<
	$(OBJCOPY) -O ihex -R .eeprom $< $@
ifneq (,$(wildcard $(TOOLSPATH)))
	$(TOOLSPATH)/teensy_post_compile -file=$(basename $@) -path=$(shell pwd) -tools=$(TOOLSPATH)
	-$(TOOLSPATH)/teensy_reboot
endif

# compiler generated dependency info
-include $(OBJS:.o=.d)

clean:
	rm -f *.o *.d $(TARGET).elf $(TARGET).hex
	rm -f $(CORES_PATH)/*.o $(CORES_PATH)/*.d
	find $(Libraries_PATH) -name "*.o" -delete
	find $(Libraries_PATH) -name "*.d" -delete

