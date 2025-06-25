# mcp3008.py
# 10 bit SPI ADC
# https://ww1.microchip.com/downloads/aemDocuments/documents/MSLD/ProductDocuments/DataSheets/MCP3004-MCP3008-Data-Sheet-DS20001295.pdf

# Quickstart usage examples:
#
# from mcp3008 import MCP3008
# myadc = MCP3008()                                 # Create class instance with default arguments
# voltage = myadc.read_voltage(5)                   # Read voltage on channel 5. read_voltage() is inherited from GenericADC bass class.
#
# Or
#
# from mcp3008 import MCP3008
# with MCP3008(5) as myadcinput:                    # Context manager protocol is supported.
#     voltage = myadcinput.read_voltage()           # Channel numbers can be specified at class creation rather than read time.



# Imports
from spidev import SpiDev # v3.6
from hardware.generic.genericADC import GenericADC



class MCP3008(GenericADC):
    def __init__(self,
            default_channel=None,   # Specify a channel number at creation rather than read time
            bus=0,                  # SPI bus
            device=0,               # SPI Chip Select
            speed_hz=1000000,       # 1MHz
            fullscale_voltage=3.3
        ):

        # Initialise parent class
        super().__init__(1023, fullscale_voltage, default_channel)

        # Save other instance parameters
        self.bus = bus
        self.device = device

        # Open SPI bus
        self.spi = SpiDev()                                                         # Default mode is correct
        self.spi.open(bus, device)
        self.spi.max_speed_hz = speed_hz



    # ADC read functions. Avoid ambiguity of just read()
    def read_int_hardware(self, channel):
        """Returns the integer Digital Output Code of the mcp3008 following a read instruction on the specified channel
           Channel must be an int from 0 to 7 inclusive.
        """
        adc_bytes = self.spi.xfer2([1, (0x08 | (channel & 0x07)) << 4, 0])
        return ((adc_bytes[1] & 3) << 8) + adc_bytes[2]                             # Read a byte and two bits. First byte received is most significant.



# Test this script if it is run directly. Beware import paths may break.
if __name__ == '__main__':
    from time import sleep
    with MCP3008() as myadc:
        while True:
            for ch in range(8):
                print(
                    "mcp3008 bus", myadc.bus,
                    "device", myadc.device,
                    "channel", ch,
                    "voltage is", myadc.read_int(ch)
                )
            print()
            sleep(1)
