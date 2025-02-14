

# MQTT settings
MQTT = {
    "broker": "mqtt.docker.local",
    "port": 1883,
    "id": "downtime-storage",
    "subscriptions": [
        {"topic": "downtime/event/+/start"},
        {"topic": "downtime/event/+/stop"},
    ],
    "base_topic_template": "downtime/state",
    "reconnect": {"initial": 5, "backoff": 2, "limit": 60},
}
