# Wrapper for using ens160 sensor over I2C

from .DFRobot_ENS160 import DFRobot_ENS160_I2C
import time


class ENS160:
    def __init__(self, bus=1, i2c_addr=0x53, ambient_temp=25.00, relative_humidity=50.00):
        """Wrapper for using the ENS160 gas sensor over I2C
        
        Users write ambient temperature and relative humidity into ENS160 for calibration and compensation of the measured gas data.
        ambient_temp Compensate the current ambient temperature, float type, unit: C
        relative_humidity Compensate the current ambient humidity, float type, unit: %rH

        Args reorderd to bus first as the user is most likely to need to change only that.
        """
        self._sensor = DFRobot_ENS160_I2C(i2c_addr, bus)
             
        while (self._sensor.begin() == False):
            """Attempt to initialize sensor. Checks that the expected chip id can be read from the i2c target."""
            print('Please check that the ENS160 is properly connected')
            time.sleep(3)

        self._sensor.set_temp_and_hum(ambient_temp, relative_humidity)


    def set_temp_and_hum(self, ambient_temp, relative_humidity):
        """Update the temperature and RH used in calculations. Useful if used alongside a temp or rh sensor. Expose sensor function externally."""
        self._sensor.set_temp_and_hum(ambient_temp, relative_humidity)


    def sample(self):
        data = dict()
        data['TVOC'] = self._sensor.get_TVOC_ppb
        data['eCO2'] = self._sensor.get_ECO2_ppm
        data['AQI'] = self._sensor.get_AQI
        return data
