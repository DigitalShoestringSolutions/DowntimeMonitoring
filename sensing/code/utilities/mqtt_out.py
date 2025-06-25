"""mqtt_out.py

Working assumptions:
	- The broker and port will not change during a session, but the topic could.
	- The user would like a one-line interaction with the MQTT system

Public API: only the function 'publish'

"""

## -- Imports ---------------------------------------------------------------------

# Standard imports
import json
import logging

# Installed imports
import paho.mqtt.publish as pahopublish

# Local imports
from utilities.timestamp import get_timestamp

## --------------------------------------------------------------------------------




## -- Settings  -------------------------------------------------------------------

default_broker = "mqtt.docker.local"
default_topic = "shoestring-sensor"
default_port = 1883
#default_qos = 0                # qos not in use

## --------------------------------------------------------------------------------




## -- Startup  --------------------------------------------------------------------

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

## --------------------------------------------------------------------------------




## -- Functions  ------------------------------------------------------------------

def publish(msg, topic=default_topic, broker=default_broker, port=default_port):
    """Add timestamp to msg (if not provided) and publish.
    Arg reordering is deliberate to allow kwargs.
    """

    # Get the timestamp first, as soon as possible after sampling
    logger.debug("requesting timestamp")
    timestamp = get_timestamp()

    # format the message
    if type(msg) is dict:                               # preferred
        # The below ordering allows the user to specify their own timestamp in the message dict if desired.
        # If an entry with key "timestamp" is not provided, one will be added using time of publication.
        # json.dumps(mydict) returns a string which is very similar to the output of str(mydict),
        #   but crucially with json.dumps() strings have double quotes as required by the json spec,
        #   while str(mydict) gives single quotes and is not recognised as json.
        payload = json.dumps({'timestamp': timestamp} | msg)

    else:                                               # failover
        payload = "timestamp: " + timestamp + " " + str(msg)

    # publish to mqtt
    logger.debug("publishing to topic: " + str(topic) + " broker: " + str(broker) + " port: " + str(port) + " the following ", str(type(payload)) + ":")
    logger.info(payload)
    pahopublish.single(topic, payload, hostname=broker, port=port) # connect, publish and disconnect in a simplified helper function
    logger.debug("MQTT publication complete")

## --------------------------------------------------------------------------------