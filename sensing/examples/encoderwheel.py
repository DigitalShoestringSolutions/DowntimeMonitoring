# This is an example file. To use it, place into code/ and rename this to main.py

# Here's an example for EncoderMonitoring:

# standard imports
from time import sleep

# local imports
from utilities.mqtt_out import publish
from hardware.generic.QuadratureEncoder import EncoderWheel

# setup sensors and models
# My quadrature encoder is connected to GPIO pins 27 and 22 (BCM numbering), has 1024 pulses per rev and circumference is 0.2 m
ConveyorEncoder = EncoderWheel(27, 22, 1024, circ=0.2)
# calling the class instance with ConveyorEncoder() returns a dictionary of position and velocity in the same units as circ

# sensing loop
while True:
    sleep(1)
    publish(ConveyorEncoder(), topic="conveyor_monitoring")