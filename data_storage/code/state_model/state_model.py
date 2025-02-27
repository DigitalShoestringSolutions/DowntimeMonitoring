import zmq
import json
import threading
from state.models import State, StatusEvent, Machine, EventSource
from state.serializers import MQTTStateSerializer
from datetime import datetime
import dateutil.parser
import logging
import traceback
from django.db import transaction

context = zmq.Context()
logger = logging.getLogger("main.state_model")


class StateModel(threading.Thread):
    def __init__(self, zmq_config):
        zmq_in_conf = zmq_config["state_in"]
        self.zmq_in = context.socket(zmq_in_conf["type"])
        if zmq_in_conf["bind"]:
            self.zmq_in.bind(zmq_in_conf["address"])
        else:
            self.zmq_in.connect(zmq_in_conf["address"])

        zmq_out_conf = zmq_config["state_out"]
        self.zmq_out = context.socket(zmq_out_conf["type"])
        if zmq_out_conf["bind"]:
            self.zmq_out.bind(zmq_out_conf["address"])
        else:
            self.zmq_out.connect(zmq_out_conf["address"])

    def start(self):
        t = threading.Thread(target=self.run)
        t.start()
        return t

    def run(self):
        # listen for incoming events
        logger.debug("listening for inbound messages")
        while True:
            try:
                msg = self.zmq_in.recv()
                msg_json = json.loads(msg)
                print("got ", msg)
                topic_parts = msg_json["topic"].split("/")
                msg_payload = msg_json["payload"]
                if topic_parts[-1] == "start" or topic_parts[-1] == "stop":
                    self.handle_message(msg_payload)
                # elif topic_parts[-1] == "custom_entry_update":
                #     self.handle_custom_field_update(msg_payload)
            except Exception:
                logger.error(traceback.format_exc())

    def handle_message(self, raw_msg):
        print(f"handling: {raw_msg}")
        try:
            # validate
            timestamp = dateutil.parser.isoparse(raw_msg["timestamp"])
            machine_id = raw_msg["machine"]
            running = raw_msg["running"]
            source = raw_msg.get("source", None)

            try:
                machine = Machine.objects.get(id=machine_id)
            except:
                pass

            # log event
            event = StatusEvent(
                target=machine,
                running=running,
                timestamp=timestamp,
                source=source if source in EventSource else None,
            )

            output = update_state(event)

            # send update
            for msg in output:
                self.zmq_out.send_json(msg)

        except Exception:
            logger.error(traceback.format_exc())


def update_state(event):
    output_messages = []
    with transaction.atomic():
        prevState = None
        try:
            prevState = State.objects.get(target__exact=event.target, end__isnull=True)

            # will throw exception if somehow there are two events without next_entries
            last_event = prevState.trigger_event
            while last_event.next_entry != None:
                last_event = last_event.next_entry

            # if event occured before last event then ignore
            if event.timestamp < last_event.timestamp:
                logger.warning(
                    f"event occured at {event.timestamp} before last event at {last_event.timestamp} -- ignoring"
                )
                return []

            event.occured_during = prevState
            event.save()

            last_event.next_entry = event
            last_event.save()

            # if event status is the same as the last state record then ignore
            if event.running == prevState.running:
                return []

            prevState.end = event.timestamp
            prevState.save()

            update_serialiser = MQTTStateSerializer(prevState)
            # exited_msg = {
            #     "record_id": prevState.record_id,
            #     "machine": str(prevState.target.id),
            #     "running": prevState.running,
            #     "start": prevState.start.isoformat(),
            #     "end": prevState.end.isoformat(),
            #     "reason": prevState.reason,
            # }

            logger.debug(f"update msg: {update_serialiser.data}")
            # send update
            output_messages.append(
                {
                    "topic": f"{str(prevState.target.id)}/update",
                    "payload": update_serialiser.data,
                }
            )

        except State.DoesNotExist:
            event.save()

        newState = State.objects.create(
            target=event.target,
            running=event.running,
            start=event.timestamp,
            trigger_event=event,
            previous_entry=prevState,
        )

    new_serializer = MQTTStateSerializer(newState)

    # entered_msg = {
    #     "record_id": newState.record_id,
    #     "machine": str(newState.target.id),
    #     "running": newState.running,
    #     "start": newState.start.isoformat(),
    #     "end": newState.end.isoformat() if newState.end else None,
    #     "reason": newState.reason,
    # }

    logger.debug(f"new msg: {new_serializer.data}")

    # send update
    output_messages.append(
        {"topic": f"{str(newState.target.id)}/new", "payload": new_serializer.data}
    )

    return output_messages
