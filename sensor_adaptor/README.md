## Node Red Analysis module for DowntimeMonitoring

This module serves a user interface on port 1883, but visiting it is not needed for configuration nor operation of this module.  
Default username: `admin`, password: `shoestring`

All configuration is done through `sensor_adaptor/config/config.json`:

## MQTT

MQTT in is the broker where the messages from the sensor are. This module subscribes to selected topics on this broker and examines the data. If you have an external sensor solution producing data relevant to downtime (eg power monitoring, throughput monitoring) 

MQTT out is where updates on the running status of the machines are sent. This can usually be left at `mqtt.docker.local`.

These two broker addresses can point to the same broker, if the sensor is already pushing data to the same broker as the rest of the Downtime solution is running on. 


## Sources

Each source is a connection between incoming MQTT messages and the running status of a machine.

`topic` is the MQTT topic to subscribe to. This needs to match where the relevant sensor is pushing data.

`filter` can be used to ignore mqtt messages that do not contain the specified key-value pairs in the JSON. This can be useful if data for multiple machines is being shared on the same topic etc.

`metric` is the JSON key for the data field that will be numerically compared. A simple comparison is done against the constant value set in `threshold`. If the value of `metric` in the sensor's MQTT message is greater than or equal to `threshold`, the machine is deemed to be running. If the value is below, it is stopped. 

`target` is the uuid (unique identifier) of the machine. This value can be found by logging into `localhost:8001/admin` and examining the machine list.

## Default configuration

The `sensor_adaptor/config/config.json` provided is an example that monitors the three different phases of a power monitoring demonstrator and uses that data to set the running status of 3 independent machines.

## Applying changes
To apply changes in `sensor_adaptor/config/config.json`, the solution needs to be stopped and restarted by running the `./stop.sh` and `./start.sh` scripts at the top level of this repository.
