# genericCT.py
# Minimal current to voltage converter
# For both AC and DC

class CurrentTransformer:

    def __init__(self, gain, offset=0):
        """A simple mathematical model for indirect proportionality
        gain: amps out per 1V in
        offset: the voltage when 0 A are flowing. The difference between the measured voltage and this value will be used to calculate the current.
        """
        self.gain = gain
        self.offset = offset

    def __call__(self, voltage):
        """Return a current in A given a voltage in V, according to the indirectly proportional relationship defined in the class instance."""
        from_neutral = voltage - self.offset
        current = self.gain * from_neutral
        return current