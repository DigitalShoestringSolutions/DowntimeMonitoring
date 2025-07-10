import traceback
import logging

logger = logging.getLogger(__name__)


class PiHat:
    ADCMax = pow(2, 12)

    def __init__(self, config, variables):
        self.channel = config.get('adc_channel')
        self.i2c_address = config.get('i2c_address',0x08)
        self.ADCVoltage = config.get('v_ref', 3.3)
        self.i2c = None
        self.channel_mask = 0x0F                            # maximum valid channel number

        self.input_variable = variables['v_in']

    def initialise(self, interface):
        self.i2c = interface

        try:
            check_device_bytes = self.i2c.read_register(self.i2c_address,0x00, 2,stop=True)
            check_device = check_device_bytes[1] << 8 + check_device_bytes[0]
            if check_device != 4:
                logger.warning(f"Grove Base Hat for RPi not detected on I2C bus")
                logger.debug(f"device_id reported: {check_device}")
        except Exception:
            logger.error(traceback.format_exc())

    def sample(self):
        try:
            # Check channel number is valid. Must be an int between 0 and self.channel_mask inclusive.
            if not isinstance(self.channel, int):
                raise TypeError("PiHat supplied with channel " + str(self.channel) + " which is a " + str(type(self.channel)) + " not an int")
                
            elif (self.channel < 0) or (self.channel > self.channel_mask):
                raise ValueError("PiHat supplied with channel number " + str(self.channel) + " cannot be negative or greater than mask " + str(self.channel_mask))

            # prepare register byte
            register_addr = 0x10 | (self.channel & self.channel_mask)

            # perform reading
            readings = self.i2c.read_register(self.i2c_address,register_addr, 2,stop=True)

            # calculate voltage
            adc_reading = (readings[1] << 8) + readings[0]
            voltage = (adc_reading / self.ADCMax) * self.ADCVoltage

            return {self.input_variable: voltage}

        except Exception as e:
            logger.error(traceback.format_exc())
            raise e
