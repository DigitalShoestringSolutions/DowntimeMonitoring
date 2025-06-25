# This is an example file. To use it, place into code/ and rename this to main.py

# This example demonstrates effortless combination of the air sensors sht40 and bmp280.
# This particular combination is important as those two are often bundled into a single package,
# but the method is designed to combine any data without a wrapper file or class.

# standard imports
from time import sleep

# local imports
from utilities.mqtt_out import publish
from hardware.ICs.sht40 import SHT40
from hardware.ICs.bmp280_wrapper import BMP280

# setup sensors and models
mysht40 = SHT40()
mybmp280 = BMP280()

# sensing loop
while True:
    sleep(1)
    publish( mysht40.get_TRH() | mybmp280.get_P() )