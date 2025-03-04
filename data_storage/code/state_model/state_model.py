import zmq
import json
from django.db.models import Q, F, Case, When, Value, Count
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

            new_states, updated_states = new_event(
                machine_id, running, timestamp, source
            )

            output = [
                make_new_state_mqtt_message(new_state) for new_state in new_states
            ]
            output.extend(
                [
                    make_update_state_mqtt_message(updated_state)
                    for updated_state in updated_states
                ]
            )

            # send update
            for msg in output:
                self.zmq_out.send_json(msg)

        except Exception:
            logger.error(traceback.format_exc())


def new_event(machine_id, running, timestamp, source):
    # can throw DoesNotExist
    machine = Machine.objects.get(id=machine_id)

    # log event
    event = StatusEvent(
        target=machine,
        running=running,
        timestamp=timestamp,
        source=source if source in EventSource else None,
    )

    return update_state(event)


def update_state(event: StatusEvent):
    new_states = []
    updated_states = []
    with transaction.atomic():
        prevState = None
        try:
            prevState = State.objects.get(target__exact=event.target, end__isnull=True)

            # get last item
            last_event = (
                StatusEvent.objects.filter(
                    Q(occured_during=prevState) | Q(resulting_state=prevState)
                )
                .order_by("-timestamp")
                .first()
            )

            # if event occured before last event then ignore
            if event.timestamp < last_event.timestamp:
                insert_old = (
                    event.target.enable_historic_sensor_input
                    and event.source == EventSource.SENSOR
                ) or (
                    event.target.enable_historic_manual_input
                    and event.source == EventSource.USER
                )

                if insert_old:
                    return insert_historic(event)
                else:
                    logger.warning(
                        f"event occured at {event.timestamp} before last event at {last_event.timestamp} -- ignoring"
                    )
                    return [], []

            event.occured_during = prevState
            event.save()

            last_event.next_entry = event
            last_event.save()

            # if event status is the same as the last state record then ignore
            if event.running == prevState.running:
                return [prevState], []  # retransmit prev_state as added

            prevState.end = event.timestamp
            prevState.save()
            updated_states.append(prevState)

        except State.DoesNotExist:
            event.save()

        newState = State.objects.create(
            target=event.target,
            running=event.running,
            start=event.timestamp,
            trigger_event=event,
            previous_entry=prevState,
        )

    new_states.append(newState)
    return new_states, updated_states


def make_new_state_mqtt_message(state: State):
    return _make_mqtt_message(state, "new")


def make_update_state_mqtt_message(state: State):
    return _make_mqtt_message(state, "update")


def make_delete_state_mqtt_message(state: State):
    return _make_mqtt_message(state, "remove")


def _make_mqtt_message(state: State, suffix):
    serializer = MQTTStateSerializer(state)
    logger.debug(f"update msg: {serializer.data}")

    return {
        "topic": f"{str(state.target.id)}/{suffix}",
        "payload": serializer.data,
    }


def insert_historic(event: StatusEvent):
    new_states = []
    updated_states = []

    # Cases:
    # 1. no active state (event before first state)
    #   * find next state
    #   * create new state using event as trigger event
    #   * set next_entry for event to trigger event of first state
    #   * next_state.previous = new_state
    #   * next_state.trigger_event.occured_during = new_state
    # 2. active state is same as event
    #   * set event occurred_during to active state
    #   * find events before and event after
    #   * adjust next_ and previous_ event to insert
    # 3. active state is different to event
    #   3a. event_after is the same -> replace as trigger event
    #       * next_state.trigger_event = event
    #       * event_after.occured_during = resulting_state
    #       * set next_state start to event timestamp
    #       * set active state end to event timestamp
    #       * event.occured_during = active_state
    #       * adjust next_ and previous_ event to insert
    #   3b. event_after is different
    #       * active_state.end = event timestamp
    #       * insert state starting at event and ending at event_after
    #       * insert state starting at event_after and ending at next_state.trigger_event
    #       * event.occured_during = active_state
    #       * adjust next_ and previous_ event to insert
    try:
        active_state = State.objects.get(  # throws error in case 1
            Q(target__exact=event.target)
            & Q(start__lte=event.timestamp)
            & (Q(end__gte=event.timestamp) | Q(end__isnull=True))
        )

        event_before = (
            StatusEvent.objects.filter(
                Q(occured_during=active_state) | Q(resulting_state=active_state)
            )
            .filter(timestamp__lte=event.timestamp)
            .select_related("next_entry")  # DB optimisation
            .order_by("-timestamp")
            .first()  # get last item
        )  # could throw an exception theoretically, but shouldn't as there must be at least a trigger event before for there to be an active state

        event_after = (
            event_before.next_entry
        )  # can throw error if no next_entry, but there has to be a next entry to be in the insert history code block

        event_before.next_entry = (
            None  # temporarily make none to prevent constraint conflicts
        )
        event_before.save()

        # Cases 2 & 3
        event.occured_during = active_state
        event_before.next_entry = event
        event.next_entry = event_after
        event.save()

        if event.running != active_state.running:  # case 3
            next_state = None
            try:
                next_state = active_state.next_entry
            except State.next_entry.RelatedObjectDoesNotExist:
                pass

            active_state.end = event.timestamp

            if event.running == event_after.running:  # case 3a
                event_after.occured_during = next_state
                if next_state:
                    next_state.trigger_event = event
                    next_state.start = event.timestamp
            else:  # case 3b
                if next_state:
                    next_state.previous_entry = (
                        None  # temporarily make none to prevent constraint conflicts
                    )
                    next_state.save()

                new_state = State.objects.create(
                    target=event.target,
                    running=event.running,
                    start=event.timestamp,
                    end=event_after.timestamp,
                    trigger_event=event,
                    previous_entry=active_state,
                )
                event_after.occured_during = new_state
                new_states.append(new_state)

                if next_state:
                    event_after_after = next_state.trigger_event
                    new_next_state = State.objects.create(
                        target=event_after.target,
                        running=event_after.running,
                        start=event_after.timestamp,
                        end=event_after_after.timestamp,
                        trigger_event=event_after,
                        previous_entry=new_state,
                    )
                    event_after_after.occured_during = new_next_state
                    next_state.previous_entry = new_next_state
                    event_after_after.save()
                else:
                    new_next_state = State.objects.create(
                        target=event_after.target,
                        running=event_after.running,
                        start=event_after.timestamp,
                        end=None,
                        trigger_event=event_after,
                        previous_entry=new_state,
                    )

                new_states.append(new_next_state)

            if next_state:
                next_state.save()
                updated_states.append(next_state)
            active_state.save()
            updated_states.append(active_state)
            event_after.save()

        event_before.save()
    except State.DoesNotExist:
        # case 1
        first_state = (
            State.objects.filter(
                target__exact=event.target,
            )
            .order_by("start")
            .first()
        )
        event.next_entry = first_state.trigger_event
        event.save()
        new_state = State.objects.create(
            target=event.target,
            running=event.running,
            start=event.timestamp,
            end=first_state.start,
            trigger_event=event,
            previous_entry=None,
        )

        first_state.previous_entry = new_state
        first_state.trigger_event.occured_during = new_state

        first_state.save()
        first_state.trigger_event.save()

        new_states.append(new_state)
        updated_states.append(first_state)

    return new_states, updated_states
