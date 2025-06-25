# installed inports
import gpiozero

# local imports
from utilities.mqtt_out import publish

# My beambreak sensor has an open-drain output that I have connected to BCM 17.
# The gpiozero.Button class defaults to asserting a pull-up and detects low as active.
EndOfConveyorBeam = gpiozero.Button(17, bounce_time=0.25)

# define a callback function to run each time the beam is broken
def on_beam_broken():
    # Publish a very boring dictionary to MQTT. A string could be sent instead, 
    # but then the message would not be JSON. 
    publish({"beam_is_broken" : 1})

# Link the callback function to the input. Note the lack of braces().
EndOfConveyorBeam.when_pressed = on_beam_broken

# Similarly, a publication of {"beam_is_broken" : 0} could be attached to Button's when_released if required
