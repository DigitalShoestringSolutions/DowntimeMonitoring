# BCRoboticsADCHAT.py
# 16 channel 10 bit analogue input HAT for Raspberry Pi
# Wrapper for two MCP3008 adcs that removes bus and device numbers from the user

# Quickstart usage examples:
#
# from BCRoboticsADCHAT import BCRoboticsADCHAT
# myadc = BCRoboticsADCHAT()                        # Create class instance with default arguments
# voltage = myadc.read_voltage(14)                  # Read voltage on channel 14. read_voltage() is inherited from GenericADC bass class.
#
# Or
#
# from BCRoboticsADCHAT import BCRoboticsADCHAT
# with BCRoboticsADCHAT(14) as myadcinput:          # Context manager protocol is supported.
#     voltage = myadcinput.read_voltage()           # Channel numbers can be specified at class creation rather than read time.



# Imports
from hardware.ICs.mcp3008 import MCP3008
from hardware.generic.genericADC import GenericADC



class BCRoboticsADCHAT(GenericADC):
    def __init__(self,
            default_channel=None,   # Specify a channel number at creation rather than read time
            speed_hz=1000000,       # 1MHz
            fullscale_voltage=3.3
        ):

        # Initialise parent class
        super().__init__(1024, fullscale_voltage, default_channel)

        # Open SPI busses
        self.mcp3008_0 = MCP3008(bus=0, device=0, speed_hz=speed_hz)    # The MCP3008 classes do not need the fullscale_voltage arg, as the calculations
        self.mcp3008_1 = MCP3008(bus=0, device=1, speed_hz=speed_hz)    #     are done in the GenericADC instance built directly off BCRoboticsADCHAT



    # ADC read functions
    def read_int_hardware(self, channel):
        if channel > 7:
            channel -= 8
            return self.mcp3008_1.read_int_hardware(channel)
        else:
            return self.mcp3008_0.read_int_hardware(channel)



# Test this script if it is run directly. Beware import paths may break.
if __name__ == '__main__':
    from time import sleep
    with BCRoboticsADCHAT() as myadc:
        while True:
            for ch in range(16):
                print(
                    "BCRoboticsADCHAT channel", ch,
                    "voltage is", myadc.read_voltage(ch)
                )
            print()
            sleep(1)
