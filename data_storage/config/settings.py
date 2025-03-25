# MQTT settings
MQTT = {
    "broker": "mqtt.docker.local",
    "port": 1883,
    "id": "downtime-storage",
    "subscriptions": [
        {"topic": "downtime/event/+/start", "qos": 1},
        {"topic": "downtime/event/+/stop", "qos": 1},
    ],
    "publish_qos": 1,
    "base_topic_template": "downtime/state",
    "reconnect": {"initial": 5, "backoff": 2, "limit": 60},
}
