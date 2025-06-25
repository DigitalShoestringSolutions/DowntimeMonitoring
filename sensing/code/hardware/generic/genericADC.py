# genericADC.py
# Base class for ADC ICs. Not hardware specific.
# Create IC library that builds on this class.
# Usage example at EoF.


class GenericADC:
    def __init__(self,
            fullscale_int,
            fullscale_voltage,
            default_channel=None
        ):

        # Save instance parameters
        self.fullscale_voltage = fullscale_voltage
        self.fullscale_int = fullscale_int
        self.default_channel = default_channel



    # Context manager support eg 'with ADC_IC() as myadc:'
    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        pass



    # ADC read functions. Avoid ambiguity of just read()
    def read_int_hardware(self, channel):
        """Return an integer representation of the ADC reading of the specified channel.
        The hardware interface used, the registers to read and the interpretation of the bytes varies greatly depending on the ADC hardware.
        Hence, this function needs to be overwritten by the hardware-specific class.
        """
        raise NotImplementedError("ADC IC library has not overwritten generic base class")


    def read_int(self, channel=None):
        """Wrapper for read_int_hardware that permits using a default channel number.
        As the class instance is not available when the default value of the kwarg is evaluated (can't do channel=self.default_channel),
        something simple (like Nonetype) must be used figuratively.
        """
        if channel is None:
            if self.default_channel is None:
                raise TypeError("Channel number must be supplied to read_ functions or provided when initialising class instance")
            channel = self.default_channel
        return self.read_int_hardware(channel)


    def read_fraction(self, channel=None):
        """Read an adc channel as a float from 0 to 1"""
        return self.read_int(channel) / self.fullscale_int


    def read_voltage(self, channel=None):
        """Read the analogue voltage at an adc pin"""
        return self.read_fraction(channel) * self.fullscale_voltage


#  Usage of the above might look like the below:
# class HardwareADC(GenericADC):
#
#     def __init__(self, fullscale_voltage=3.3):
#
#         # Initialise parent class
#         super().__init__(1024, fullscale_voltage)      # for a 10 bit ADC that outputs integers from 0 to 1024
#
#         # other hardware init behaviour here
#
#     def read_int_hardware(self, channel):
#
#         set_channel(channel)
#         extracted_int = "clock bits out of ADC and assemble into integer"
#
#         return extracted_int
#
#
# The default_channel argument, not used in the example above,
# allows a channel number to be saved at creation time, rather than passed on every read_.
# The is an optional kwarg, hence it must be supplied to GenericADC last.
# However, it is recommended to make this the first arg of a child class so it can be the only one:
# class HardwareADC(GenericADC):
#     def __init__(self, default_channel=None, fullscale_voltage=3.3):
#
#         # Initialise parent class
#         super().__init__(1024, fullscale_voltage, default_channel)
#
# Allows very neat usage such as
# with HardwareADC(4) as myadc:
#     voltage = myadc.read_voltage()