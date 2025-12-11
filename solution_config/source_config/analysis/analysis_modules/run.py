"""Configure analysis module as a downtime monitoring sensor adaptor.

Compares sensor readings to thresholds and posts alerts to MQTT if the comparison result changes.

One analysis module instance per sensor-machine link.

"""

import logging
import datetime

# Internal module imports
from trigger.engine import TriggerEngine
import config_manager
import paho.mqtt.publish as pahopublish
import json


# Parse command-line arguments and configure logging again based on those
args = config_manager.handle_args()
logging.basicConfig(level=args["log_level"])
logger = logging.getLogger(__name__)

# Load configuration from config files
config = config_manager.get_config(
    args.get("module_config_file"), args.get("user_config_file")
)

# Initialize the trigger engine with loaded configuration
trigger = TriggerEngine(config)

## -------------

# Default values for global variables
OldRunningVal = None # value (bool) will be added after first comparision
OldRunningTime = "2021-01-01T00:00:00+00:00" # timestamp when alert status was last published. Default to a time in the past that will parse

# Load config - outside of function
broker = config["sensor"]["broker"]
topic = config["sensor"]["topic"]
parameter_name = config["thresholds"]["parameter"]
threshold = float(config["thresholds"]["value"])
target = config["output"]["target"]

# Main function
@trigger.mqtt.event(topic)  # TODO: how can the broker to subscribe to be loaded from config? How does it get passed to this?
async def thresholds(topic, payload, config={}): 
    """Receives an MQTT message, compares the contained temperature reading to thresholds and send a new MQTT message with the topic suffix `/alerts`

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
    machine = payload.get("machine", "NoMachineNameInMQTTMessage")
    logger.debug(f"Downtime thresholds comparison received parameter {parameter_name} value {parameter_value} on topic {topic} for machine {machine} at {timestamp}, comparing to threshold {threshold}")
        
    # compare reading to thresholds
    if parameter_value > threshold:
        Running = 1
    else:
        Running = 0
    logger.debug(f"Running status for machine {machine} calculated as {Running}")

    # iif results have changed, or previous output was more than 1h ago, publish result.
    SendUpdate = False
    if (Running != OldRunningVal):
        SendUpdate = True
        logger.info(f"Machine {machine} running status changed to {Running} as {parameter_name} passing threshold {threshold} at {timestamp}")

    if (datetime.datetime.fromisoformat(timestamp) > (datetime.datetime.fromisoformat(OldAlertTime) + datetime.timedelta(hours=1))):
        SendUpdate = True
        logger.info(f"Sending repeat RunningVal {Running} message for machine {machine} as previous update was > 1h ago")

    if SendUpdate:
        # Prepare message variables
        output_payload = {
            "timestamp"     : timestamp,
            "machine"       : machine,          # Pass through for debug info
            "running"       : Running,
            "source"        : "sensor",
            "Threshold"     : threshold,        # Pass through for debug info
        }

        # Publish to MQTT
        logger.debug(f"Publishing machine {target} RunningVal {Running} to mqtt.docker.local topic: {target}")
        pahopublish.single(topic=target, payload=json.dumps(output_payload), hostname="mqtt.docker.local", retain=True)
        logger.debug(f"publication to {broker} complete")


    else:
        pass # New message would be a repeat of the old, don't spam. Sounds like a good idea until the broker crashes and loses the retained message.
        # Could have separate mqtt topics for every result vs only update on changes, but then why does the change-only topic exist?
        logger.debug(f"RunningVal {Running} unchanged, not publishing")


    # Save result for next time
    OldRunningVal = Running
    OldAlertTime = timestamp


# Start the trigger engine and its scheduler/event loops
trigger.start()
