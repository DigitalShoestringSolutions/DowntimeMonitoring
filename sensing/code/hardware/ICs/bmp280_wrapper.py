# bmp280_wrapper.py

# Uses Pimoroni's https://github.com/pimoroni/bmp280-python 

# Public API: all functions of the BMP280 class

# imports
from bmp280 import BMP280 as pmBMP280
from smbus2 import SMBus

class BMP280:

  def __init__(self, i2cbus=1, i2caddr=0x76):
    self.i2cbus=i2cbus
    self.i2caddr=i2caddr
    
  def get_P(self):
    """Read only the pressure from the bmp280. 
    As this sensor is primarily a pressure sensor, it's likely that's the only reading you care about
    """
    with SMBus(self.i2cbus) as bus:
      data = dict()
      data['pressure'] = round(pmBMP280(i2c_addr=self.i2caddr, i2c_dev=bus).get_pressure(), 3)
    return data

  def get_T(self):
    """Read only the temperature from the bmp280"""
    with SMBus(self.i2cbus) as bus:
      data = dict()
      data['temperature'] = round(pmBMP280(i2c_addr=self.i2caddr, i2c_dev=bus).get_temperature(), 3)
    return data
    
  def get_TP(self):
    """Read both the temperature and pressure from the bmp280 in a single bus instance.
    Marginly more efficient than (get_P | get_TP )
    """
    with SMBus(self.i2cbus) as bus:
      mybmp280 = pmBMP280(i2c_dev=bus)
      data = dict()
      data['pressure'] = round(mybmp280.get_pressure(), 3)
      data['temperature'] = round(mybmp280.get_temperature(), 3)
    return data

# Test if run directly. Beware import paths may break. 
if __name__ == '__main__':
  from time import sleep
  testbmp280 = BMP280()
  while True:
    print("BMP280 test")
    print("T only:", testbmp280.get_T(), "degC")
    print("P only:", testbmp280.get_P(), "hPa")
    TP = testbmp280.get_TP()
    print("Combined:", TP)
    print("T combined:", TP['temperature'], "degC")
    print("P combined:", TP['pressure'], "hPa")
    print()
    sleep(1)
