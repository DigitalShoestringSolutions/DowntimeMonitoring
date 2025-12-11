"""Configure analysis module for temperature monitoring.

Compares temperature readings to thresholds and posts alerts to MQTT if the comparison result changes.

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

# Default value for global variables
OldAlertVals = {} # machine-specific values will be added after first comparision
OldAlertTimes = {} # machine-specific timestamps when alert status was last published

# Main function
@trigger.mqtt.event("temperature_monitoring/+")   # Subscribe to single depth only (machine names) to avoid regurgitating its own messages.
async def thresholds(topic, payload, config={}):  # per-machine class instances would be nice, to make saving context easier than global vars
    """Receives an MQTT message, compares the contained temperature reading to thresholds and send a new MQTT message with the topic suffix `/alerts`

    :param str topic:    The resolved topic of the incomming MQTT message
    :param dict payload: The payload of the incomming MQTT message, expecting json loaded as dict
    :param dict config:  The module config
    """
    global OldAlertVals  # allow this func to save previous value in global variable
    global OldAlertTimes

    # extract machine name, temperature reading and timestamp from payload
    machine = payload["machine"]
    temperature = float(payload["temperature"])
    timestamp = payload["timestamp"]
    logger.debug(f"Temperature thresholds comparison received temperature {temperature} for machine {machine} at {timestamp}")
    
    # extract previous alert value for this machine from global variable
    OldAlertVal = OldAlertVals.get(machine, None)
    OldAlertTime = OldAlertTimes.get(machine, "2021-01-01T00:00:00+00:00")  # Default to a time in the past that will parse

    # extract thresholds from machine-specific config
    machine_thresholds = config["thresholds"]["machines"].get(machine, config["thresholds"]["default"])
    high_threshold = float(machine_thresholds["high"]["value"])
    high_hyst = float(machine_thresholds["high"]["hyst"])
    low_threshold = float(machine_thresholds["low"]["value"])
    low_hyst = float(machine_thresholds["low"]["hyst"])
    logger.debug(f"comparing temperature {temperature} on machine {machine} to high threshold {high_threshold} (-{high_hyst}) and low threshold {low_threshold} (+{low_hyst})")
    
    # compare temperature reading to thresholds
    if temperature > high_threshold:
        AlertVal = 1
    elif temperature > (high_threshold - high_hyst) and OldAlertVal == 1:
        AlertVal = 1
    elif temperature < low_threshold:
        AlertVal = -1
    elif temperature < (low_threshold + low_hyst) and OldAlertVal == -1:
        AlertVal = -1
    else:
        AlertVal = 0
    logger.debug(f"AlertVal for {machine} calculated as {AlertVal}")

    # iif results have changed, or previous output was more than 1h ago, publish result. The option to publish regardless could be made configurable.
    SendUpdate = False
    if (AlertVal != OldAlertVal):
        SendUpdate = True
        logger.info(f"Machine {machine} temperature {temperature} passing thresholds {low_threshold} (+{low_hyst}) and {high_threshold} (-{high_hyst}) at {timestamp}")

    if (datetime.datetime.fromisoformat(timestamp) > (datetime.datetime.fromisoformat(OldAlertTime) + datetime.timedelta(hours=1))):
        SendUpdate = True
        logger.info(f"Sending repeat AlertVal message for Machine {machine} at temperature {temperature} as previous update was > 1h ago")

    if SendUpdate:
        # Prepare message variables
        output_payload = {
            "timestamp"     : timestamp,
            "machine"       : machine,
            "AlertVal"      : AlertVal,
            "ThresholdLow"  : low_threshold,                      # Including threshold values just as a FYI for debugging
            "ThresholdHigh" : high_threshold,
        }
        broker = config.get("output_broker", "mqtt.docker.local") 
        topic = topic + "/alerts"                                 # Alerts suffix to topic could be configurable but not implementing until some demand

        # Publish to MQTT
        logger.info(f"Publishing machine {machine} AlertVal {AlertVal} to broker: {broker} topic: {topic}")
        pahopublish.single(topic=topic, payload=json.dumps(output_payload), hostname=broker, retain=True)
        logger.debug(f"publication to {broker} complete")


    else:
        pass # New message would be a repeat of the old, don't spam. Sounds like a good idea until the broker crashes and loses the retained message.
        # Could have separate mqtt topics for every result vs only update on changes, but then why does the change-only topic exist?
        logger.debug(f"AlertVal {AlertVal} unchanged, not publishing")


    # Save result for next time
    OldAlertVals[machine] = AlertVal
    OldAlertTimes[machine] = timestamp


# Start the trigger engine and its scheduler/event loops
trigger.start()
