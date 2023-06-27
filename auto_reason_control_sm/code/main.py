# Check config file is valid
# create BBs
# plumb BBs together
# start BBs
# monitor tasks

# packages
import tomli
import time
import logging
import zmq
# local
import mqtt_publisher
import state_model
import mqtt_subscriber

logger = logging.getLogger("main")
logging.basicConfig(level=logging.INFO)  # move to log config file using python functionality


def get_config():
    with open("./config/config.toml", "rb") as f:
        toml_conf = tomli.load(f)
    logger.info(f"config:{toml_conf}")
    return toml_conf


def config_valid(config):
    if config.get("debug"):
        logger.info("setting level to debug")
        # TODO work out how to fix
        logging.basicConfig(level=logging.DEBUG)
    return True


def create_building_blocks(config):
    bbs = {}

    mqtt_sub_out = {"type": zmq.PUSH, "address": "tcp://127.0.0.1:4000", "bind": True}
    state_in = {"type": zmq.PULL, "address": "tcp://127.0.0.1:4000", "bind": False}
    state_out = {"type": zmq.PUSH, "address": "tcp://127.0.0.1:4001", "bind": True}
    mqtt_pub_in = {"type": zmq.PULL, "address": "tcp://127.0.0.1:4001", "bind": False}

    bbs["mqtt_subscriber"] = mqtt_subscriber.MQTTSubscriber(config, mqtt_sub_out)
    bbs["state_model"] = state_model.StateModel(config, {'in': state_in, 'out': state_out})
    bbs["mqtt_pubisher"] = mqtt_publisher.MQTTPublisher(config, mqtt_pub_in)

    logger.debug(f"bbs {bbs}")
    return bbs


def start_building_blocks(bbs):
    for key in bbs:
        p = bbs[key].start()


def monitor_building_blocks(bbs):
    while True:
        time.sleep(1)
        for key in bbs:
            # logger.debug(f"{bbs[key].exitcode}, {bbs[key].is_alive()}")
            # todo actually monitor
            pass


if __name__ == "__main__":
    conf = get_config()
    # todo set logging level from config file
    if config_valid(conf):
        bbs = create_building_blocks(conf)
        start_building_blocks(bbs)
        monitor_building_blocks(bbs)
    else:
        raise Exception("bad config")
