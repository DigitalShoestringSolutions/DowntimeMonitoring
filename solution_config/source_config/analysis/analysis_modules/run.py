"""Configure analysis module as a downtime monitoring sensor adaptor.

Compares sensor readings to thresholds and posts alerts to MQTT if the comparison result changes.

One analysis module instance per sensor-machine link.
Use the recipe to create multiple sensor adaptor module instances if you would like automatic downtime event creation on multiple machines.

"""

import logging
import datetime

# Internal module imports
from trigger.engine import TriggerEngine
import config_manager
import paho.mqtt.publish as pahopublish
import json
import time
import sys


# Parse command-line arguments and configure logging again based on those
args = config_manager.handle_args()
logging.basicConfig(level=args["log_level"])
logger = logging.getLogger(__name__)

# Load configuration from config files
config = config_manager.get_config(
    args.get("module_config_file"), args.get("user_config_file")
)

if config.get("module_enabled") == False:
    logger.info("Analysis module is disabled, sleeping for an hour before restarting")
    time.sleep(3600)
    sys.exit(0)

# Initialize the trigger engine with loaded configuration
trigger = TriggerEngine(config)

## -------------

# Default values for global variables
OldRunningVal = None # value (bool) will be added after first comparision
OldRunningTime = "2021-01-01T00:00:00+00:00" # timestamp when status was last published. Default to a time in the past that will parse

# Load config - outside of function
#broker = config["sensor"]["broker"]  # not needed here - input_broker is passed directly to MQTTTrigger via trigger.engine.mqtt ...
topic = config["sensor"]["topic"]
parameter_name = config["thresholds"]["parameter"]
threshold = float(config["thresholds"]["value"])
target = config["output"]["target"]

# Main function
@trigger.mqtt.event(topic)
async def thresholds(topic, payload, config={}):
    """Receives an MQTT message, compares the contained reading to thresholds and send a new MQTT message to the downtime solution.

    :param str topic:    The resolved topic of the incomming MQTT message
    :param dict payload: The payload of the incomming MQTT message, expecting json loaded as dict
    :param dict config:  (optional) The module config (not used)
    """
    global OldRunningVal  # allow this func to save previous value in global variable
    global OldRunningTime

    # extract sensor reading and timestamp from payload
    parameter_value = float(payload[parameter_name])
    timestamp = payload["timestamp"]

    # Also extract other info that won't be used
    machine = payload.get("machine", target)  # use UUID from config if no machine name found in sensor MQTT message
    logger.debug(f"Downtime thresholds comparison received parameter {parameter_name} value {parameter_value} on topic {topic} for machine {machine} at {timestamp}, comparing to threshold {threshold}")

    # compare reading to thresholds
    if parameter_value > threshold:
        Running = True
    else:
        Running = False
    logger.debug(f"Running status for machine {machine} calculated as {Running}")

    # iif results have changed, or previous output was more than 1h ago, publish result.
    SendUpdate = False
    if (Running != OldRunningVal):
        SendUpdate = True
        logger.info(f"Machine {machine} id {target} running status changed to {Running} as {parameter_name} passing threshold {threshold} at {timestamp}")

    if (datetime.datetime.fromisoformat(timestamp) > (datetime.datetime.fromisoformat(OldRunningTime) + datetime.timedelta(hours=1))):
        SendUpdate = True
        logger.info(f"Sending repeat RunningVal {Running} message for machine {machine} as previous update was > 1h ago")

    if SendUpdate:
        # Prepare message variables
        output_payload = {
            "timestamp"     : timestamp,
            "machine"       : target,  # duplicate with topic? As usual.
            "running"       : Running,
            "source"        : "sensor"
        }

        topic = 'downtime/event/' + target
        if Running:
            topic = topic + '/start'
        else:
            topic = topic + '/stop'


        # Publish to MQTT
        logger.debug(f"Publishing machine {machine} RunningVal {Running} to mqtt.docker.local topic: {target}")
        pahopublish.single(topic=topic, payload=json.dumps(output_payload), hostname="mqtt.docker.local", retain=True)
        logger.debug(f"publication to mqtt.docker.local complete")


    else:
        logger.debug(f"RunningVal {Running} for machine {machine} unchanged, not publishing")


    # Save result for next time
    OldRunningVal = Running
    OldRunningTime = timestamp


# Start the trigger engine and its scheduler/event loops
trigger.start()
