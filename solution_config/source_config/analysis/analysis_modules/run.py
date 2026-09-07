"""Configure analysis module as a downtime monitoring sensor adaptor.

Compares sensor readings to thresholds and posts alerts to MQTT if the comparison result changes.

One analysis module instance per sensor-machine link.
Use the recipe to create multiple sensor adaptor module instances if you would like automatic downtime event creation on multiple machines.

"""

import logging
import datetime

# Internal module imports
from trigger.engine import TriggerEngine
from analysis.threshold import apply_threshold
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
# Load config - outside of function
# broker = config["sensor"]["broker"]  # not needed here - input_broker is passed directly to MQTTTrigger via trigger.engine.mqtt ...
topic = config["sensor"]["topic"]
target = config["output"]["target"]
mqtt_host = config.get("mqtt", {}).get("broker", "mqtt.docker.local")

# Construct threshold engine configuration mapping target machine ID
threshold_config = {
    target: {
        "threshold_value": float(config["thresholds"]["value"]),
        "threshold_parameter_name": config["thresholds"]["parameter"],
        "timestamp_parameter_name": config["thresholds"].get(
            "timestamp_parameter", "timestamp"
        ),
        "smoothing_factor": float(config["thresholds"].get("smoothing_factor", 1.0)),
        "debounce_seconds": float(config["thresholds"].get("debounce_seconds", 0.0)),
        "retransmit_interval_seconds": float(
            config["thresholds"].get("retransmit_interval", 3600.0)
        ),
    }
}


# Main function
@trigger.mqtt.event(topic)
async def thresholds(topic, payload, config={}):
    """Receives an MQTT message, compares the contained reading to thresholds and send a new MQTT message to the downtime solution.

    :param str topic:    The resolved topic of the incomming MQTT message
    :param dict payload: The payload of the incomming MQTT message, expecting json loaded as dict
    :param dict config:  (optional) The module config (not used)
    """
    eval_threshold = apply_threshold(threshold_config, target)

    result = await eval_threshold(payload)

    if result is None:
        logger.debug(
            f"No output required (state unchanged or debouncing) for topic {topic}"
        )
        return

    running, event_ts = result
    formatted_ts = event_ts.isoformat()

    output_payload = {
        "timestamp": formatted_ts,
        "machine": target,
        "running": running,
        "source": "sensor",
    }

    output_topic = f"downtime/event/{target}/" + ("start" if running else "stop")

    logger.debug(
        f"Publishing machine {target} running={running} at {formatted_ts} to {mqtt_host} topic: {output_topic}"
    )
    pahopublish.single(
        topic=output_topic,
        payload=json.dumps(output_payload),
        hostname=mqtt_host,
        retain=True,
    )
    logger.debug("Publication to MQTT complete")


# Start the trigger engine and its scheduler/event loops
trigger.start()
