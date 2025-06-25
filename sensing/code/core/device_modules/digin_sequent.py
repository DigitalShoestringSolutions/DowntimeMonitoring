"""Driver for the Sequent Microsystems 8 and 16 digital input HATs

https://sequentmicrosystems.com/products/16-universal-inputs-card-for-raspberry-pi
https://sequentmicrosystems.com/products/eight-hv-digital-inputs-for-raspberry-pi

Public API: all public methods of Sequent16inputsHAT and Sequent8inputsHAT
"""


## -- Imports ---------------------------------------------------------------------

# Standard imports
#none

# Installed inports
import smbus2

# Local imports
#none

## --------------------------------------------------------------------------------


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


    def __init__(self, stack: int = 0, bus: int = 1):
        """Class for reading data from the Sequent Microsystems 8 and 16 digital input HATs.

        https://sequentmicrosystems.com/products/16-universal-inputs-card-for-raspberry-pi.
        https://sequentmicrosystems.com/products/eight-hv-digital-inputs-for-raspberry-pi

        stack (default 0): The address offset set by jumpers/DIP switches on the HAT. No jumpers or all off = stack 0.
        bus (default 1): The number of the i2c bus the device responds on, passed to smbus2.
        """

        # Validate stack input
        if stack < 0 or stack > 7 or not isinstance(stack, int):
            raise ValueError('Invalid stack level ' + type(stack) + ' ' + str(stack) + ' , must be int 0-7 inclusive')

        # Calculate device I2C address as offset by stack number.
        # 7 bit address (will be left shifted to add the read write bit)
        # Flip stack bits with XOR. Stack 0 has address 0x27, each stack decrements that until stack 7 is at 0x20
        self._hw_addr = 0x20 + (0x07 ^ stack)   # No other need to save stack

        # Save other args
        self._bus = bus


    def _extract_channel(self, status_reg, channel):
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
            return 1
        else:
            return 0


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
        with smbus2.SMBus(self._bus) as i2cbus:
            status_reg = i2cbus.read_word_data(self._hw_addr, self._DIGITAL_INPUTS_STATUS_REGISTER_ADDRESS)

        # Return a 16 bit integer.
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

# Test this script if it is run directly

if __name__ == '__main__':
    print("testing sequent_digital_inputs.py")
    from time import sleep

    # HATs to test
    myhats = [
        Sequent16DigitalInputs(0),
    #    Sequent8DigitalInputs(1),
    #    Sequent16DigitalInputs(2),
    ]

    for myhat in myhats:

        print("testing read_single_channel()")
        for ch in myhat._channel_map:
            print("channel", ch , "is", myhat.read_single_channel(ch))
            sleep(0.1) # don't saturate I2C bus

        print("testing _readbits()")
        raw = myhat._readbits()
        print("    raw reg is", '{:016b}'.format(raw)) # padded to match below

        print("testing read_all_channels()") # without using _extract_channel()
        all = myhat.read_all_channels()
        print("all inputs are", '{:016b}'.format(all), all)
        for ch in myhat._channel_map:
            print("from all, channel", ch, "is", 1 if all & (1 << (ch-1)) else 0)

        print("testing read_multiple_channels()")
        multi = myhat.read_multiple_channels([1,2,3,4])
        print("multi:", multi)
        print()

        #print("testing channel number validation with invalid channel numbers")
        #print("channel 17 is", myhat.read_single_channel(17))
        #print("channel foo is", myhat.read_single_channel('foo'))
        print()
