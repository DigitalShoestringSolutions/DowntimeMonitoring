# Sensing service module

The purpose of this Shoestring Service Module is to collect data from locally attached sensors, and publish it to an MQTT broker.  
Sensors will typically be attached via I2C, SPI, USB or GPIO.  
The broker may be hosted on the same device or remotely.  

## Structure & Usage

This structure is designed to be minimal and flexible.  
The use case must supply a `main.py` into `config/`.  
The use case may also supply a `requirements.txt` into `config/`.  

<ul>
  
  If using [the Assembler](https://github.com/DigitalShoestringSolutions/ShoestringAssembler), this can be inserted via `UserConfig/Sensing/main.py` and `UserConfig/Sensing/requirements.txt`.  
  See [the Starter Solution Template](https://github.com/DigitalShoestringSolutions/starter-solution-template/tree/template/assembler) for more detail. 
</ul>

`requirements.txt` will be passed to `pip` to install PyPi packages into the sensing docker container. If none are required, the requirements file can be omitted.  

Although `main.py` runs as code, it can be short and serves as the config file. Some deployments can run with as little as 6 simple lines of code here - half of which are `import time`, `while True:` and `time.sleep(1)`.

`main.py` is supported by other scripts sorted into `utilities`, `hardware.ICs` and `hardware.generic` (for models etc)

Common imports will include:  
- `from utilities.mqtt_out import publish` - a simple wrapper for the paho mqtt client that provides all necessary interaction with the MQTT system. This function has only one required argument (a message), but `topic`, `broker`, and `port` can also be specified in that order or as kwargs.

## Output interfaces

The messages published to MQTT will be strings. Where `publish()` is supplied with a python dictionary, an ISO8601 timestamp will be added as another entry in the dictionary under key `'timestamp'` and the combined dictionary cast to a string that uses double quotes for string-literals (i.e. JSON). This is the preferred method of operation.  
In case a dictionary is not supplied, the message will be cast to string and `timestamp: 2024-05-02T09:35:00.241090+00:00 ` will be inserted at the start of the string.

## Examples

Some inspiration for what could be written in `main.py` are given in the `examples` directory.
