"""Sequent_16chADC.py
16 channel, 12 bit analogue input HAT for Raspberry Pi
Simple driver for using the hardware only as an ADC.
https://sequentmicrosystems.com/products/sixteen-analog-digital-inputs-8-layer-stackable-hat-for-raspberry-pi


Quickstart usage examples:

from Sequent_16chADC import Sequent_16chADC
myadc = Sequent_16chADC()                         # Create class instance with default arguments.
voltage = myadc.read_voltage(14)                  # Read voltage on channel 14. read_voltage() is inherited from GenericADC bass class.

Or

from Sequent_16chADC import Sequent_16chADC
with Sequent_16chADC(14) as myadcinput:           # Context manager protocol is supported.
    voltage = myadcinput.read_voltage()           # Channel numbers can be specified at class creation rather than read time.
"""


# Imports
from smbus2 import SMBus
from hardware.generic.genericADC import GenericADC




class Sequent_16chADC(GenericADC):
    def __init__(self,
            default_channel=None,       # Specify a channel number at creation rather than read time
            stack=0,                    # In place of i2c address, use the Sequent stack selection system
            i2cbus=1,
            fullscale_voltage=10        # Nominal analogue range
        ):

        # Initialise parent class.
        # It is a 12 bit ADC, but conversion to voltage is done on HAT hardware.
        # The value in the register is in millivolts.
        super().__init__(10000, fullscale_voltage, default_channel)

        # Calculate device I2C address as offset by stack number.
        # 7 bit address (will be left shifted to add the read write bit)
        # Stack 0 has address 0x58, each stack increments that until stack 7 is at 0x5f
        self.i2caddr = 0x58 + stack   # No other need to save stack

        # Save other instance parameters
        self.i2cbus = i2cbus


    # ADC read functions
    def read_int_hardware(self, channel):
        """Returns the integer clocked out of the ADC following a read instruction on the specified channel
           Channel must be an int from 1 to 16 inclusive.
           0-10V ADC data is stored as mV words in registers 6 to 36
        """
        with SMBus(self.i2cbus) as bus:
            return bus.read_word_data(self.i2caddr, 6 + ((channel - 1) * 2))


    # Other functions
    def get_firmware_version(self):
        """Get firmware version of attached HAT.

        Returns: (str) MAJOR.MINOR firmware version number
        """
        with SMBus(self.i2cbus) as bus:
            version_major = bus.read_byte_data(self.i2caddr, 221)
            version_minor = bus.read_byte_data(self.i2caddr, 222)
        version = str(version_major) + "." + str(version_minor)
        return version




# Test this script if it is run directly. Beware import paths may break.
if __name__ == '__main__':
    from time import sleep
    with Sequent_16chADC() as myadc:
        while True:
            for ch in range(1, 17):
                print(
                    "Sequent_16chADC channel", ch,
                    "int is", myadc.read_int(ch),
                    "voltage is", myadc.read_voltage(ch)
                )
            print()
            sleep(1)
