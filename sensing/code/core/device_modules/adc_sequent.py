import traceback
import logging

logger = logging.getLogger(__name__)


class Sequent16chADC:
    ADCMax = 10000 # conversion to mV done on hardware

    def __init__(self, config, variables):
        self.channel = config.get('adc_channel')            # No default value here, must be configured
        self.i2c_address = config.get('i2c_address',0x58)   # Use stack number?
        self.ADCVoltage = config.get('v_ref', 10)           # 10V max reading range
        self.i2c = None                                     # Interface created in initialise()
        self.channel_mask = 16                              # maximum valid channel number

        self.input_variable = variables['v_in']

    def initialise(self, interface):
        self.i2c = interface

    def sample(self):
        try:
            # Check channel number is valid. Must be an int between 1 and self.channel_mask inclusive.
            if not isinstance(self.channel, int):
                raise TypeError("Sequent16chADC supplied with channel " + str(self.channel) + " which is a " + str(type(self.channel)) + " not an int")

            elif (self.channel < 1) or (self.channel > self.channel_mask):  # As marked on silkscreen, this ADC's lowest channel is 1.
                raise ValueError("Sequent16chADC supplied with channel number " + str(self.channel) + " cannot be negative or greater than mask " + str(self.channel_mask))

            # prepare register byte
            register_addr = 6 + ((self.channel - 1) * 2)

            # perform reading. If stop=True, readings can glitch when monitoring multiple machines simultaneously.
            readings = self.i2c.read_register(self.i2c_address, register_addr, 2, stop=False)

            # calculate voltage
            adc_reading = (readings[1] << 8) + readings[0]
            voltage = (adc_reading / self.ADCMax) * self.ADCVoltage     # In this particular case could also directly divide by 1000

            return {self.input_variable: voltage}

        except Exception as e:
            logger.error(traceback.format_exc())
            raise e
