import paho.mqtt.client as mqtt
import multiprocessing
import logging
import zmq
import json
import time
import traceback
from urllib.parse import urljoin

context = zmq.Context()
logger = logging.getLogger("main.wrapper")


class MQTTServiceWrapper(multiprocessing.Process):

    def __init__(self, mqtt_conf, zmq_conf):
        super().__init__()

        self.url = mqtt_conf["broker"]
        self.port = int(mqtt_conf["port"])
        self.client_id = mqtt_conf["id"]

        self.topic_base = mqtt_conf["base_topic_template"]
        self.subscriptions = mqtt_conf.get("subscriptions",[])

        if mqtt_conf.get("reconnect"):
            self.initial = mqtt_conf["reconnect"].get("initial", 5)
            self.backoff = mqtt_conf["reconnect"].get("backoff", 2)
            self.limit = mqtt_conf["reconnect"].get("limit", 60)
        else:
            self.initial = 5
            self.backoff = 2
            self.limit = 60

        # declarations
        self.zmq_conf = zmq_conf
        self.zmq_in = None
        self.zmq_out = None

    def do_connect(self):
        zmq_in_conf = self.zmq_conf["wrapper_in"]
        self.zmq_in = context.socket(zmq_in_conf["type"])
        if zmq_in_conf["bind"]:
            self.zmq_in.bind(zmq_in_conf["address"])
        else:
            self.zmq_in.connect(zmq_in_conf["address"])

        zmq_out_conf = self.zmq_conf["wrapper_out"]
        self.zmq_out = context.socket(zmq_out_conf["type"])
        if zmq_out_conf["bind"]:
            self.zmq_out.bind(zmq_out_conf["address"])
        else:
            self.zmq_out.connect(zmq_out_conf["address"])

    def mqtt_connect(self, client, first_time=False):
        timeout = self.initial
        exceptions = True
        while exceptions:
            try:
                if first_time:
                    client.connect(self.url, self.port, 60)
                else:
                    logger.error("Attempting to reconnect...")
                    client.reconnect()
                logger.info("Connected!")
                time.sleep(self.initial)  # to give things time to settle
                exceptions = False
            except Exception:
                logger.error(f"Unable to connect, retrying in {timeout} seconds")
                time.sleep(timeout)
                if timeout < self.limit:
                    timeout = timeout * self.backoff
                else:
                    timeout = self.limit

    def on_connect(self, client, _userdata, _flags, rc):
        logger.info("Connected with result code " + str(rc))
        # do subscribe
        for entry in self.subscriptions:
            if 'topic' in entry:
                qos = entry.get('qos', 0)
                topic = entry['topic']
                logger.info(f"Subscribing to {topic} at QOS {qos}")
                client.subscribe(topic, qos)

    def on_message(self, _client, _userdata, msg):
        try:
            output = {"topic": msg.topic, "payload": json.loads(msg.payload)}
            logger.info(f"Forwarding {output}")
            self.zmq_out.send_json(output)
        except:
            logger.error(f"Invalid json message - ingoring: {traceback.format_exc()}")

    def on_disconnect(self, client, _userdata, rc):
        if rc != 0:
            logger.error(f"Unexpected MQTT disconnection (rc:{rc}), reconnecting...")
            self.mqtt_connect(client)

    def run(self):
        self.do_connect()

        client = mqtt.Client(client_id=self.client_id)
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.on_disconnect = self.on_disconnect

        # self.client.tls_set('ca.cert.pem',tls_version=2)
        logger.info(f"connecting to {self.url}:{self.port}")
        self.mqtt_connect(client, True)

        run = True
        while run:
            try:
                while self.zmq_in.poll(50, zmq.POLLIN):
                    try:
                        msg = self.zmq_in.recv(zmq.NOBLOCK)
                        msg_json = json.loads(msg)
                        topic = (
                            f"{self.topic_base}/{msg_json['topic']}"
                            if self.topic_base
                            else msg_json["topic"]
                        )
                        msg_payload = msg_json["payload"]
                        logger.debug(f"pub topic:{topic} msg:{msg_payload}")
                        client.publish(topic, json.dumps(msg_payload))
                    except zmq.ZMQError:
                        pass
                client.loop(0.05)
            except Exception as e:
                logger.error(traceback.format_exc())
