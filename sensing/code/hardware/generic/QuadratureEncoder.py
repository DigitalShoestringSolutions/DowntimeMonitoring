# QuadratureEncoder.py

# standard imports
import time

# installed imports
from gpiozero import RotaryEncoder


class EncoderWheel():

    def __init__(self, Apin, Bpin, steps_per_rev, circ=None, dia=None):
        """Uses gpiozero.RotaryEncoder. Specify either circ or dia."""
        self.encoder = RotaryEncoder(Apin, Bpin, max_steps=0)
        self._steps_per_rev = steps_per_rev
        self._veloctiy_old_steps = 0
        self._velocity_old_time = time.time()

        if circ is None:
            if dia is None:
                raise TypeError("Either wheel circumference or diameter needs to be specified!")
            else:
                self._circ = 3.14159265359*dia
        else:
            self._circ = circ

    def __call__(self, rounding=3):
        """Return a dict containing current position and velocity
        Rounding should be either None or an int of decimal places"""
        return {
            "position": self.get_current_position(rounding),
            "velocity": self.get_current_velocity(rounding) 
            }


    def get_current_position(self, rounding=None):
        """Return the current tangential displacement of the wheel, in the units of circ or dia supplied.
        Rounding should be either None or an int of decimal places.
        Position can be reset with .encoder.steps = 0, no wrapper needed
        """

        dist = self._circ*self.encoder.steps/self._steps_per_rev

        if rounding is None:
            return dist
        else:
            return round(dist, rounding)


    def get_current_velocity(self, rounding=None):
        """Returns the average velocity since this function was last called
        Rounding should be either None or an int of decimal places.
        """

        # read position and timestamp
        new_steps = self.encoder.steps
        new_time = time.time()

        # Calculate detla
        delta_steps = new_steps - self._veloctiy_old_steps
        delta_time = new_time - self._velocity_old_time
        vel = (self._circ*delta_steps/self._steps_per_rev) / delta_time
        
        # Save read position and timestamp for next time
        self._veloctiy_old_steps = new_steps
        self._velocity_old_time = new_time

        if rounding is None:
            return vel
        else:
            return round(vel, rounding)
