"""Driver for the Sequent Microsystems 8 and 16 digital input HATs

https://sequentmicrosystems.com/products/16-universal-inputs-card-for-raspberry-pi
https://sequentmicrosystems.com/products/eight-hv-digital-inputs-for-raspberry-pi

Public API: all public methods of Sequent16inputsHAT and Sequent8inputsHAT
"""


## -- Imports ---------------------------------------------------------------------

# Standard imports
import traceback
import logging

# Installed inports
#none

# Local imports
#none

## --------------------------------------------------------------------------------


logger = logging.getLogger(__name__)


class Sequent16DigitalInputs:

    # I2C register to read from to get the status of the inputs
    _DIGITAL_INPUTS_STATUS_REGISTER_ADDRESS = 0x00

    # For each channel, which bit in the read word represents its state?
    # It is a trivial sequential mapping for the 16 input card, but this explicit format makes supporting the 8 input easy.
    _channel_map = {
        1  : 0x8000,
        2  : 0x4000,
        3  : 0x2000,
        4  : 0x1000,
        5  : 0x0800,
        6  : 0x0400,
        7  : 0x0200,
        8  : 0x0100,
        9  : 0x0080,
        10 : 0x0040,
        11 : 0x0020,
        12 : 0x0010,
        13 : 0x0008,
        14 : 0x0004,
        15 : 0x0002,
        16 : 0x0001,
    }

    def __init__(self, config, variables):
        """Class for reading data from the Sequent Microsystems 8 and 16 digital input HATs.

        https://sequentmicrosystems.com/products/16-universal-inputs-card-for-raspberry-pi.
        https://sequentmicrosystems.com/products/eight-hv-digital-inputs-for-raspberry-pi

        """
        self.channel = config.get('gpio_channel')
        self.i2c_address = config.get('i2c_address', 0x27)

        self.i2c = None
        self.input_variable = variables['dig_in']


    def initialise(self, interface):
        self.i2c = interface


    def sample(self) -> dict:
        """Report the status of single channel.
        Returns a dictionary with single entry key variables['dig_in'] and the value is the status of self.channel
        """
        try:
            status_report = {self.input_variable: self.read_single_channel(self.channel)}
            logger.debug("digin_sequent returning sample: %s", status_report)
            return status_report

        except Exception as e:
            logger.error(traceback.format_exc())
            raise e


    def _extract_channel(self, status_reg, channel) -> int:
        """Use the register status and channel map to deduce to status of a single channel.
        Bits are complemented (flipped) and not necessarily in order.
        """

        # Validate channel input
        if not isinstance(channel, int):
            raise TypeError('Channel must be int, received ' + str(type(channel)) + ' ' + channel)

        if not channel in self._channel_map:
            raise ValueError('Invalid channel number: ' + str(channel) + ', must be integer in ' + str(list(self._channel_map.keys()))) # list keys


        # Extract value. Bits are complemented (bit 0 => voltage high, bit 1 => voltage low)
        if status_reg & self._channel_map[channel] == 0:
            channelstatus = 1
        else:
            channelstatus = 0

        # Report and return status
        logger.debug("Extracted channel " + str(channel) + " status as " + str(channelstatus))
        return channelstatus


    def read_single_channel(self, channel: int) -> int:
        """Read the status of all inputs, but return only a single bit corresponding to the specified channel.

        Channel numbers are 1 to 8 or 1 to 16 to match the silkscreen on the hardware.
        """

        # Read register
        status_reg = self._readbits()

        # Process result
        return self._extract_channel(status_reg, channel)


    def read_multiple_channels(self, channel_numbers: list) -> list:
        """Read the status of all inputs, but return only selected ones.

        channel_numbers: List of channel numbers (1 to 8 or 1 to 16 to match the silkscreen on the hardware) to be read.
        More efficient than reading the channels individually (only a single I2C transaction),
        but easier to pass than read_all_channels().
        Returns a list of bits describing the status of each input channel, in the order of the supplied list.
        """

        # Read register
        status_reg = self._readbits()

        # Iterate over required channels
        ret = []
        for channel in channel_numbers:

            # Extract status of individual channel and store
            ret.append(self._extract_channel(status_reg, channel))

        return ret


    def read_all_channels(self) -> int:
        """Read the status of all inputs and return as a single n-bit number.

        Lower channel numbers are less significant bits in the returned value.
        Requires keys of _channel_map to be positive non-zero integers.
        """

        # Read register
        status_reg = self._readbits()

        # Process result.
        ret = 0
        for channel in self._channel_map:
            if self._extract_channel(status_reg, channel):  # if voltage high
                ret += 1 << (channel - 1) 	                # Assuming ch1 is the first channel, it needs no bit shifting
        return ret


    def _readbits(self) -> int:
        """Read the raw status of the inputs.

        Returns a 16 bit number with one bit representing each input channel.
        Which bit refers to which channel is defined in _channel_map.
        Bit status is the complement of the voltage at the pin.
        """

        # Use a context manager to handle errors on the bus
        buffer_out = self.i2c.read_register(self.i2c_address, self._DIGITAL_INPUTS_STATUS_REGISTER_ADDRESS, 2)
        status_reg = (buffer_out[1] << 8) + buffer_out[0] # equlivalent to if smbus2's read_word_data was done directly

        # Return a 16 bit integer.
        logger.debug("Sequent digital inputs had read status bits as " + bin(status_reg))
        return status_reg


class Sequent8DigitalInputs(Sequent16DigitalInputs):
    _channel_map = {
        1: 0x0800,
        2: 0x0400,
        3: 0x0200,
        4: 0x0100,
        5: 0x0010,
        6: 0x0020,
        7: 0x0040,
        8: 0x0080,
    }


## --------------------------------------------------------------------------------
