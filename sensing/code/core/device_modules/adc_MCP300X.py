import traceback
import logging

logger = logging.getLogger(__name__)


class MCP3008:
    channel_mask = 0b0111
    ADCMax = pow(2, 10)
    spi_mode = 3

    def __init__(self, config, variables):
        self.channel = config.get('adc_channel')
        self.differential = config.get('differential', False)
        self.ADCVoltage = config.get('v_ref', 3.3)
        self.spi = None

        self.input_variable = variables['v_in']

    def initialise(self, interface):
        self.spi = interface

    def sample(self):
        try:
            # Check channel number is valid. Must be an int between 0 and self.channel_mask inclusive.
            if not isinstance(self.channel, int):
                raise TypeError("MCP300X supplied with channel " + str(self.channel) + " which is a " + str(type(self.channel)) + " not an int")

            elif (self.channel < 0) or (self.channel > self.channel_mask):
                raise ValueError("MCP300X supplied with channel number " + str(self.channel) + " cannot be negative or greater than mask " + str(self.channel_mask))

            # prepare config byte
            config_byte = ((0b1000 if self.differential else 0b0) | (self.channel & self.channel_mask))
            # perform reading
            buffer_out = self.spi.transfer([1, config_byte << 4, 0],
                                           mode=self.spi_mode)  # [ start_bit, config_byte, empty ]
            # calculate voltage
            adc_reading = ((buffer_out[1] & 0b11) << 8) + buffer_out[2]
            voltage = (adc_reading / self.ADCMax) * self.ADCVoltage
            return {self.input_variable: voltage}

        except Exception as e:
            logger.error(traceback.format_exc())
            raise e

class MCP3004(MCP3008):
    channel_mask = 0b0011  # only has 4 channels
    pass
