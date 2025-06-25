"""main.py that prepares the Sensing service module (lite-v0.6.0) for Downtime Monitoring.

Publishes simple MQTT messages indicating if a machine name is running. These messages are to be picked up by the sensor adaptor.

All configuration is done in the Settings section.
Assumes sensors have pulls external to the GPIO interface.
"""

## -- Imports ---------------------------------------------------------------------

# Standard imports
import time

# Installed inports
#none used directly, but smbus2 is used by sequent_digital_inputs

# Local imports
from utilities.mqtt_out import publish
from hardware.ICs.sequent_digital_inputs import Sequent8DigitalInputs, Sequent16DigitalInputs

## --------------------------------------------------------------------------------




## -- Settings  -------------------------------------------------------------------

# List of machines to be monitored by local sensors.
machines = (
# machine name, input channel number, input state when machine is active
("Machine_Name_Here", 1, 1),   # input 1 is high when Machine_Name_Here is running
("Machine_2", 3, 0),           # input 3 is low when Machine_2 is running
# duplicate the above line to add more machines
)

# Timing
sample_interval = 5 # seconds between reporting on each machine

# Hardware input interface - select which HAT you are using by uncommenting it (remove the leading #)
input_interface = Sequent8DigitalInputs()
#input_interface = Sequent16DigitalInputs()

## --------------------------------------------------------------------------------




## -- Main Loop -------------------------------------------------------------------

while True:

    for machine in machines:                                            # For each machine in the list defined in settings
        input_state = input_interface.read_single_channel(machine[1])     # Read sensor
        running = True if input_state == machine[2] else False            # Compare sensor value to config
        publish( {                                                        # Publish the following to MQTT:
            "machine" : machine[0],                                         # string machine name
            "running" : running,                                            # bool
            }, "equipment_monitoring/status/" + machine[0])                 # Topic to publish to, including machine name

    time.sleep(sample_interval)                                         # Idle between samples


## --------------------------------------------------------------------------------
