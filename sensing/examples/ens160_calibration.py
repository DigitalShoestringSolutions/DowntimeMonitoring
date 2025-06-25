# This is an example file. To use it, place into code/ and rename this to main.py

# This example demonstrates using data from one sensor to calibrate another,
# and selecting which data to keep when you have multiple sensors that could measure the same thing

# standard imports
from time import sleep

# local imports
from utilities.mqtt_out import publish
from hardware.ICs.sht40 import SHT40
from hardware.ICs.bmp280_wrapper import BMP280
from hardware.ICs.ens160 import ENS160

# setup sensors and models
mysht40 = SHT40()
mybmp280 = BMP280()
myens160 = ENS160()

# sensing loop
while True:
    # Persay you want to use the humidity reading from the SHT40 and the temperature reading from the BMP280 to calibrate the ENS160.
    sleep(1)
    sht40readings = mysht40.get_TRH()
    bmp280readings = mybmp280.get_TP()

    myens160.set_temp_and_hum(bmp280readings['temperature'], sht40readings['humidity'])

    # Temperature reading from the SHT0 is submitted. When dicts with conflicting keys are combined with dict1 | dict 2, the values from dict2 are kept.
    publish( bmp280readings | sht40readings | myens160.sample())