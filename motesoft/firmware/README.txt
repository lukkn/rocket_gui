Instructions to build code:

STEP 1
* Open the folder platformio_build in the arduino IDE
* MAKE SURE Teensyduino IS INSTALLED!!!

STEP 2
* Make sure the board selected in the arduino IDE is Teensy 4.1
* If it gives you an error about "sensors_and_servos.h" not found, copy the folder lib/sensors_and_servos into your arduino libraries folder, or make a symlink
	> A symlink is probably better, because if you copy the code into the arudino library and then edit it there, it won't make it into any git commits unless you specifically copy it back
* If you're on Windows, it should be the arudino libraries folder in "Program Files (x86)/Arduino/Libraries"
* If it complains about any other libraries not being installed, install them using the arduino library manager

STEP 3
* Connect the mote board to your computer with an appropriate cable
* Press the "deploy" button in the arduino IDE
* When prompted by Teensyduino, press the button on the mote board
* It should say "done deploying" or something like that
* SEE NEXT STEP **BEFORE** USING MOTE OR POWERING IT WITH A DC POWER SUPPLY

STEP 4
* Make sure the MOTE board is powered either via USB or by a DC Power Supply, NOT BOTH
* If powered via usb, take care to make sure it is only via some kind of hub. Plugging it directly into a computer might damage said computer, do so only at own risk.
* Connect MOTE to a control computer via ethernet, and via USB if you need to read serial outputs (see above note about not combining DC/USB power and about PC saftey with usb)
* Disconnect from BU wifi when communicating with mote via ethernet
* Run the GUI in the Client_GUI folder (see the README file there)
* Make sure the GUI is reading the correct config csv file, and that it is configured correctly.
