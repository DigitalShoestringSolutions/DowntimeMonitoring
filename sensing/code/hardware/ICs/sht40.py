# Minimal file for use of sht40 sensor
# Written from https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/products/unit/ENV%E2%85%A3%20Unit/SHT40.pdf

# Future features: heater, cropping of RH values, validating checksum, calibration...

# Public API: only the get_TRH() function of the SHT40 class

# imports
from smbus2 import SMBus, i2c_msg
from time import sleep

class SHT40:

  _COMMAND_MEASURE_TRH = 0xFD # measure T & RH with high precision & repeatability

  def __init__(self, i2cbus=1, i2caddr=0x44):
    self.i2cbus = i2cbus
    self.i2caddr = i2caddr


  def _read(self):
    """Read bytes containing temperature and humidity data from the i2c bus"""
    with SMBus(self.i2cbus) as bus:

      # ask the sensor to take a reading
      bus.i2c_rdwr(i2c_msg.write(self.i2caddr, [self._COMMAND_MEASURE_TRH]))

      # allow time for the sensor to take a valid reading
      sleep(0.01)

      # Clock the reading out of the sensor
      msg = i2c_msg.read(self.i2caddr, 6)
      bus.i2c_rdwr(msg)

      # Post process data
      read_bytes = list(msg)
      # Checksums could be validated here. For now this can be done manually with a tool such as:
      # http://www.sunshine2k.de/coding/javascript/crc/crc_js.html and the custom settings on page 9 of 
      # https://m5stack.oss-cn-shenzhen.aliyuncs.com/resource/docs/products/unit/ENV%E2%85%A3%20Unit/SHT40.pdf
      S_T = (read_bytes[0] << 8) | (read_bytes[1])
      S_RH = (read_bytes[3] << 8) | (read_bytes[4])

    return S_T, S_RH

  def _calculate_temperature(self, S_T):
    """Calculate a temperature from adc int"""
    T_degC = -45 + (175*S_T/65535)
    return T_degC

  def _calculate_relativehumidity(self, S_RH):
    """Calculate a relative humidity from adc int"""
    RH = -6 + (125*S_RH/65535)
    return RH

  def get_TRH(self):
    readings = self._read()
    data = dict()
    data['temperature'] = round(self._calculate_temperature(readings[0]), 3)       # degC
    data['humidity'] = round(self._calculate_relativehumidity(readings[1]), 3)     # %
    return data

# Test if run directly. Beware import paths may break. 
if __name__ == '__main__':
  from time import sleep
  mysht40 = SHT40()
  while True:
    TRH = mysht40.get_TRH()
    print("T: ", TRH['temperature'], "degC")
    print("RH:", TRH['humidity'], "%")
    print()
    sleep(1)
