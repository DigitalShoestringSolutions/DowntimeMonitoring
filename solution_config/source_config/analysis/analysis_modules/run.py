"""Configure analysis module as a downtime monitoring sensor adaptor.

Compares sensor readings to thresholds and posts alerts to MQTT if the comparison result changes.

One analysis module instance per sensor-machine link.
Use the recipe to create multiple sensor adaptor module instances if you would like automatic downtime event creation on multiple machines.

"""

import datetime
import json
import logging
import sys
import time
from typing import Any, Optional

# Internal module imports
from analysis.threshold import apply_threshold
import config_manager
import paho.mqtt.publish as pahopublish
from trigger.engine import TriggerEngine

# Parse command-line arguments and configure logging again based on those
args = config_manager.handle_args()
logging.basicConfig(level=args["log_level"])
logger = logging.getLogger(__name__)

# Load configuration from config files
config = config_manager.get_config(
    args.get("module_config_file"), args.get("user_config_file")
)

if config.get("module_enabled") is False:
    logger.info("Analysis module is disabled, sleeping for an hour before restarting")
    time.sleep(3600)
    sys.exit(0)

# Initialize the trigger engine with loaded configuration
trigger = TriggerEngine(config)


def _optional_float(val: Any) -> Optional[float]:
    if val is None or val == "":
        return None
    return float(val)


## -------------
# Load config - outside of function
# broker = config["sensor"]["broker"]  # not needed here - input_broker is passed directly to MQTTTrigger via trigger.engine.mqtt ...
topic = config["sensor"]["topic"]
target = config["output"]["target"]
mqtt_host = config.get("mqtt", {}).get("broker", "mqtt.docker.local")

thresholds_cfg = config["thresholds"]

# Construct threshold engine configuration mapping target machine ID
threshold_config = {
    target: {
        "mode": thresholds_cfg.get("mode", "ema_debounce"),
        "threshold_value": float(thresholds_cfg["value"]),
        "threshold_parameter_name": thresholds_cfg["parameter"],
        "timestamp_parameter_name": thresholds_cfg.get(
            "timestamp_parameter", "timestamp"
        ),
        # EMA + Debounce options
        "smoothing_factor": float(thresholds_cfg.get("smoothing_factor", 1.0)),
        "debounce_seconds": float(thresholds_cfg.get("debounce_seconds", 0.0)),
        # Leaky Integrator options
        "integral_threshold": _optional_float(thresholds_cfg.get("integral_threshold")),
        "decay_rate": float(thresholds_cfg.get("decay_rate", 1.0)),
        "integral_max": _optional_float(thresholds_cfg.get("integral_max")),
        # Pure Integrator options
        "integration_window_seconds": _optional_float(
            thresholds_cfg.get("integration_window_seconds")
        ),
        "integration_time_unit_seconds": float(
            thresholds_cfg.get("integration_time_unit_seconds", 1.0)
        ),
        # Common time-guard & retransmit options
        "max_gap_seconds": _optional_float(thresholds_cfg.get("max_gap_seconds")),
        "retransmit_interval_seconds": float(
            thresholds_cfg.get("retransmit_interval", 3600.0)
        ),
    }
}

# Initialize evaluator at startup so invalid mode configurations fail fast
eval_threshold = apply_threshold(threshold_config, target)


# Main function
@trigger.mqtt.event(topic)
async def thresholds(topic, payload, config={}):
    """Receives an MQTT message, compares the contained reading to thresholds and send a new MQTT message to the downtime solution.

    :param str topic:    The resolved topic of the incomming MQTT message
    :param dict payload: The payload of the incomming MQTT message, expecting json loaded as dict
    :param dict config:  (optional) The module config (not used)
    """
    result = await eval_threshold(payload)

    if result is None:
        logger.debug(
            f"No output required (state unchanged, debouncing, or integrating) for topic {topic}"
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
