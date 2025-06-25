# ads1115.py
# 16 bit I2C ADC.
# https://www.ti.com/lit/ds/symlink/ads1115.pdf

# Quickstart usage examples:
#
# from ads1115 import ADS1115
# myadc = ADS1115()                                 # Create class instance with default arguments
# voltage = myadc.read_voltage(2)                   # Read voltage on channel 2. read_voltage() is inherited from GenericADC bass class.
#
# Or
#
# from ads1115 import ADS1115
# with ADS1115(2) as myadcinput:                    # Context manager protocol is supported.
#     voltage = myadcinput.read_voltage()           # Channel numbers can be specified at class creation rather than read time.



# Imports
from smbus2 import SMBus # v0.4.3
from hardware.generic.genericADC import GenericADC
from time import sleep


class ADS1115(GenericADC):
    def __init__(self,
            default_channel=None,       # Specify a channel number at creation rather than read time
            i2cbus=1,
            i2caddr=0x48,
            fullscale_voltage=2.048     # Power On Reset fullscale is 2.048V.
        ):

        # Initialise parent class. It is a 16 bit ADC, but it uses two's complement.
        super().__init__(32767, fullscale_voltage, default_channel)

        # Save other instance parameters
        self.i2cbus = i2cbus
        self.i2caddr = i2caddr



    # ADC read functions. Avoid ambiguity of just read()
    def read_int_hardware(self, channel):
        """Returns the integer following clocked out of the ADC following a read instruction on the specified channel
           Channel must be an int from 0 to 3 inclusive.
        """
        with SMBus(self.i2cbus) as bus:
            # resend config before every sample rather than at init time, in case of hotplugging or corruption
            # prep config for single-ended conversion, FSR=6.144V, continous, 128SPS, comparator off. See datasheet p28.
            config = [(0b01 << 6) | (channel << 4) | (0b000 << 1) | (0b0), ( (0b100 << 5) | (0b00011) )]
            self.fullscale_voltage=6.144
            # write 2 config bytes to config word register at address 0x01
            bus.write_i2c_block_data(self.i2caddr, 0x01, config)

            # Read 2 bytes from register 0. Using bus.read_word_data puts the bytes the worng way round.
            adc_bytes = bus.read_i2c_block_data(self.i2caddr, 0x00, 2)
            adc_int = (adc_bytes[0] << 8) | adc_bytes[1]
            return adc_int



# Test this script if it is run directly. Beware import paths may break.
if __name__ == '__main__':
    from time import sleep
    with ADS1115 as myadc:
        while True:
            for ch in range(4):
                print(
                    "ADS1115 bus", myadc.i2cbus,
                    "address", myadc.i2caddr,
                    "channel", ch,
                    "voltage is", myadc.read_voltage(ch)
                )
            print()
            sleep(1)
