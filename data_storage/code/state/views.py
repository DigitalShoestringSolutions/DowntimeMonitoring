from django.db.models import Q, F, Case, When, Value, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.paginator import Paginator
from rest_framework import viewsets, status
from django.db import transaction
from rest_framework.decorators import (
    action,
    api_view,
    permission_classes,
    renderer_classes,
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework_csv.renderers import CSVRenderer
import datetime
import dateutil.parser

from .models import State, StatusEvent, Machine, EventSource
from stop_reasons.models import Reason
from .serializers import (
    StateSerializer,
    EventSerializer,
    MachineSerializer,
    MQTTStateSerializer,
    PrettyStateSerializer,
    NestedStateSerialiser,
)
import json
import zmq

context = zmq.Context()


@api_view(("GET",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer))
def getMachines(request):
    operations_qs = Machine.objects.all()
    serializer = MachineSerializer(operations_qs, many=True)
    return Response(serializer.data)


@api_view(("PUT",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer))
def setReason(request, record_id):
    record = get_object_or_404(State, record_id=record_id)

    reason_id = request.data["reason"]
    if reason_id is None:
        reason = None
    else:
        reason = get_object_or_404(Reason, id=reason_id)

    record.reason = reason
    record.save()

    # Send MQTT event
    mqtt_serializer = MQTTStateSerializer(record, many=False)
    try:
        conf = settings.ZMQ_CONFIG["state_out"]
        socket = context.socket(conf["type"])
        socket.connect(conf["address"])
        socket.send_json(
            {
                "topic": f"{str(record.target.id)}/update",
                "payload": mqtt_serializer.data,
            }
        )
    except:
        raise

    serializer = StateSerializer(record, many=False)
    return Response(serializer.data)


@api_view(("PUT",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer))
def updateEvent(request, event_id):
    event = get_object_or_404(StatusEvent, event_id=event_id)

    # permissions
    machine = event.target
    if (not machine.edit_manual_input and event.source == EventSource.USER) or (
        not machine.edit_sensor_input and event.source == EventSource.SENSOR
    ):
        return Response(
            {
                "error": "no_permission",
                "reason": "Editting this event is not permitted for this machine",
            },
            status=401,
        )

    new_timestamp_raw = request.data["timestamp"]
    try:
        new_timestamp = datetime.datetime.fromisoformat(new_timestamp_raw)
    except:
        return Response(
            {"reason": "'timestamp' is not a valid iso8601 timestamp"}, status=400
        )

    # Check boundaries
    previous_event = None
    try:
        previous_event = event.previous_entry
    except StatusEvent.previous_entry.RelatedObjectDoesNotExist:
        pass  # no previous entry
    next_event = event.next_entry

    if next_event and new_timestamp >= next_event.timestamp:
        return Response(
            {
                "error": "too_late",
                "reason": "Can't update event timestamp to be after the next event that occured",
                "limit": next_event.timestamp,
            },
            status=400,
        )

    if previous_event and new_timestamp <= previous_event.timestamp:
        return Response(
            {
                "error": "too_early",
                "reason": "Can't update event timestamp to be before the previous event that occured",
                "limit": previous_event.timestamp,
            },
            status=400,
        )

    # do updates
    event.timestamp = new_timestamp

    try:
        caused_state = event.resulting_state
        caused_state.start = new_timestamp
        caused_state.save()

        prior_state = caused_state.previous_entry
        if prior_state:
            prior_state.end = new_timestamp
            prior_state.save()

    except StatusEvent.resulting_state.RelatedObjectDoesNotExist:
        pass  # does not have a caused_state

    event.save()

    return Response()


@api_view(("DELETE",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer))
def deleteEvent(request, event_id):
    event = get_object_or_404(StatusEvent, event_id=event_id)

    # permissions
    machine = event.target
    if (not machine.edit_manual_input and event.source == EventSource.USER) or (
        not machine.edit_sensor_input and event.source == EventSource.SENSOR
    ):
        return Response(
            {
                "error": "no_permission",
                "reason": "Deleting this event is not permitted for this machine",
            },
            status=401,
        )

    with transaction.atomic():
        # get surrounding events
        next_event = event.next_entry
        previous_event = None
        try:
            previous_event = event.previous_entry
            previous_event.next_entry = next_event  # bridge event once removed
        except StatusEvent.previous_entry.RelatedObjectDoesNotExist:
            pass  # no previous entry

        try:
            # Cases:
            # 1. no caused state - no state changes
            # 2. next event is repeated status - shift forward
            #     * update caused_state.trigger_event to next_event
            #     * next_event.occured_during = prior_state
            #     * caused_state.start = next_event.timestamp
            #     * prior_state.end = next_event.timestamp
            # 3. next event is repeated, but no prior state:
            #     * update caused_state.trigger_event to next_event
            #     * caused_state.start = next_event.timestamp
            # 4. next event is different status - remove caused state and merge prior and next
            #     * update prior_state.end to next_state.end
            #     * prior_state.next_entry = next_state.next_entry
            #     * change all occured_during events for caused and next to prior
            #     * remove caused state
            #     * remove next_state
            # 5. next event is different status - no next event
            #     * update prior_state.end to null
            #     * prior_state.next_entry to null
            #     * change all occured_during events for caused to prior
            #     * remove caused state
            # 6. next event is different status - no prior event
            #     * next_state.previous_entry to null
            #     * remove caused_state
            # 7 next event is different status - no prior, no next
            #     * remove caused_state

            caused_state = event.resulting_state
            prior_state = caused_state.previous_entry

            if next_event.running == event.running:  # Cases 2 & 3
                caused_state.trigger_event = next_event
                caused_state.start = next_event.timestamp
                caused_state.save()

                if prior_state:  # Case 2 only
                    next_event.occured_during = prior_state
                    next_event.save()
                    prior_state.end = next_event.timestamp
                    prior_state.save()
            else:  # Cases 4 - 7
                next_state = None
                try:
                    next_state = caused_state.next_entry
                except State.next_entry.RelatedObjectDoesNotExist:
                    pass  # no next state

                next_next_state = None
                try:
                    next_next_state = next_state.next_entry
                except State.next_entry.RelatedObjectDoesNotExist:
                    pass  # no next state

                if prior_state and next_state:  # Case 4
                    prior_state.end = next_state.end
                    if next_next_state:
                        next_next_state.previous_entry = prior_state

                    next_state.events_during.update(occured_during=prior_state)
                    next_state.delete()
                elif prior_state and next_state is None:  # Case 5
                    prior_state.end = None
                    prior_state.next_entry = None
                elif prior_state is None and next_state:  # Case 6
                    next_state.previous_entry = None
                    next_state.save()

                if prior_state:  # Cases 4 & 5
                    caused_state.events_during.update(occured_during=prior_state)
                    prior_state.save()

                caused_state.delete()  # all cases

                if (
                    next_next_state
                ):  # must be after caused_state is deleted to avoid unique constraint conflict on previous entry in one-to-one
                    next_next_state.save()

        except StatusEvent.resulting_state.RelatedObjectDoesNotExist:
            pass  # Case 1

        event.delete()
        if previous_event:
            previous_event.save()

    return Response()


@api_view(("GET",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer, CSVRenderer))
def snapshot(request, machine_id=None):
    at = request.GET.get("t", None)
    page = int(request.GET.get("page", 0))
    page_length = request.GET.get("page-length", None)
    q = Q(end__isnull=True)

    if at:
        at_dt = dateutil.parser.isoparse(at)  # parse "at" to datetime
        q = (q | Q(end__gte=at_dt)) & Q(start__lte=at_dt)

    if machine_id:
        q = q & Q(target__id__exact=machine_id)

    qs = State.objects.filter(q).order_by("-start", "-record_id")

    if page_length:
        paginator = Paginator(qs, page_length)
        try:
            qs_slice = paginator.page(page if page > 0 else 1)
        except:
            qs_slice = []
        serializer = StateSerializer(qs_slice, many=True)
    else:
        serializer = StateSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(("GET",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer, CSVRenderer))
def history(request, machine_id=None):
    t_start = request.GET.get("from", None)
    t_end = request.GET.get("to", None)
    running = request.GET.get("running", None)
    pretty = request.GET.get("pretty", False)
    wrap = request.GET.get("wrap", False) == "true"
    page = int(request.GET.get("page", 0))
    page_length = request.GET.get("page-length", None)
    duration_str = request.GET.get("duration", None)

    q = Q()

    serializer_class = PrettyStateSerializer if pretty == "true" else StateSerializer

    if running:
        q = q & Q(running=running == True)

    start_dt = None
    if t_start:
        start_dt = dateutil.parser.isoparse(t_start)
        q = q & Q(end__gte=start_dt) | Q(end__isnull=True)

    end_dt = None
    if t_end:
        end_dt = dateutil.parser.isoparse(t_end)
        q = q & Q(start__lte=end_dt)

    if machine_id:
        q = q & Q(target__id__exact=machine_id)

    if duration_str:
        try:
            duration = float(duration_str)
            q = q & (
                Q(end__gte=F("start") + datetime.timedelta(minutes=duration))
                | Q(end__isnull=True)
            )
        except ValueError:
            pass  # duration was not valid - ignore

    qs = State.objects.filter(q).order_by("-start", "-record_id")
    if page_length:
        paginator = Paginator(qs, page_length)
        try:
            qs_slice = paginator.page(page if page > 0 else 1)
        except:
            qs_slice = []
        serializer = serializer_class(
            qs_slice,
            many=True,
            context={"wrap": wrap, "start": start_dt, "end": end_dt},
        )
    else:
        serializer = serializer_class(
            qs,
            many=True,
            context={"wrap": wrap, "start": start_dt, "end": end_dt},
        )
    return Response(serializer.data)


@api_view(("GET",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer, CSVRenderer))
def eventsForMachine(request, machine_id):
    t_start = request.GET.get("from", None)
    t_end = request.GET.get("to", None)
    print(f"all events {t_start}>{t_end}")

    q = Q(target__id__exact=machine_id)

    if t_start:
        start_dt = dateutil.parser.isoparse(t_start)
        q = q & Q(timestamp__gte=start_dt)

    if t_end:
        end_dt = dateutil.parser.isoparse(t_end)
        q = q & Q(timestamp__lte=end_dt)

    qs = StatusEvent.objects.filter(q).order_by("-start", "-record_id")
    serializer = EventSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(("GET",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer, CSVRenderer))
def eventsForMachineByState(request, machine_id):
    t_start = request.GET.get("from", None)
    t_end = request.GET.get("to", None)
    running = request.GET.get("running", None)
    page = int(request.GET.get("page", 0))
    page_length = request.GET.get("page-length", None)

    q = Q()

    if running:
        q = q & Q(running=running == True)

    if t_start:
        start_dt = dateutil.parser.isoparse(t_start)
        q = q & Q(end__gte=start_dt) | Q(end__isnull=True)

    if t_end:
        end_dt = dateutil.parser.isoparse(t_end)
        q = q & Q(start__lte=end_dt)

    if machine_id:
        q = q & Q(target__id__exact=machine_id)

    qs = (
        State.objects.filter(q)
        .order_by("-start", "-record_id")
        .prefetch_related("events_during")
    )

    if page_length:
        paginator = Paginator(qs, page_length)
        try:
            qs_slice = paginator.page(page if page > 0 else 1)
        except:
            qs_slice = []
        serializer = NestedStateSerialiser(qs_slice, many=True)
    else:
        serializer = NestedStateSerialiser(qs, many=True)
    return Response(serializer.data)


@api_view(("GET",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer, CSVRenderer))
def downtime(request, machine_id=None):

    machine_results, reason_results, machine_reason_results = do_get_downtime(
        request, machine_id
    )

    machine_outputs = [
        {
            **values,
            "machine": target.name,
        }
        for target, values in machine_results.items()
    ]
    reason_outputs = [
        {"reason": reason.text if reason is not None else "Unspecified", **values}
        for reason, values in reason_results.items()
    ]

    machine_reasons = [
        {
            "machine": machine.name,
            "reason": reason.text if reason is not None else "Unspecified",
            **metrics,
        }
        for machine, values in machine_reason_results.items()
        for reason, metrics in values.items()
    ]
    
    return Response(
        {
            "machines": machine_outputs,
            "reasons": reason_outputs,
            "machine_reasons": machine_reasons,
        }
    )


def do_get_downtime(request, machine_id):
    t_query_start = request.GET.get("from", None)
    t_query_to = request.GET.get("to", None)

    q = ~Q(reason__considered_downtime=False)

    start_query_from_dt = None
    if t_query_start:
        start_query_from_dt = dateutil.parser.isoparse(t_query_start)
        q = q & Q(end__gte=start_query_from_dt) | Q(end__isnull=True)

    end_query_to_dt = None
    if t_query_to:
        end_query_to_dt = dateutil.parser.isoparse(t_query_to)
        q = q & Q(start__lte=end_query_to_dt)

    if machine_id:
        q = q & Q(target__id__exact=machine_id)

    qs = (
        State.objects.filter(q)
        .order_by("start")
        .select_related("target")  # DB optimisation
        .select_related("reason")  # DB optimisation
    )

    machine_results = {}
    reason_results = {}
    machine_reason_results = {}
    for entry in qs:
        # output init
        if entry.target not in machine_results:
            machine_results[entry.target] = {"running": 0, "stopped": 0, "count": 0}
            machine_reason_results[entry.target] = {}

        # timestamp windowing
        end_ts = window_timestamp(
            value_or_default_to_now(entry.end), upper_limit=end_query_to_dt
        )
        start_ts = window_timestamp(entry.start, lower_limit=start_query_from_dt)

        # duration calculation
        duration = (end_ts - start_ts).total_seconds()

        # assign to machine
        if entry.running:
            machine_results[entry.target]["running"] += duration
        else:
            machine_results[entry.target]["stopped"] += duration
            machine_results[entry.target]["count"] += 1

        if entry.running == False:
            # assign to reason
            if entry.reason not in reason_results:
                reason_results[entry.reason] = {"total_duration": 0, "count": 0}

            reason_results[entry.reason]["total_duration"] += duration
            reason_results[entry.reason]["count"] += 1

            # assign to machine-reason pairing
            if entry.reason not in machine_reason_results[entry.target]:
                machine_reason_results[entry.target][entry.reason] = {
                    "total_duration": 0,
                    "count": 0,
                }

            machine_reason_results[entry.target][entry.reason][
                "total_duration"
            ] += duration
            machine_reason_results[entry.target][entry.reason]["count"] += 1

    return machine_results, reason_results, machine_reason_results


@api_view(("GET",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer, CSVRenderer))
def windowed_downtime(request):
    t_start = request.GET.get("from", None)
    t_end = request.GET.get("to", None)
    bucket = request.GET.get("bucket", "day")
    machine_id = request.GET.get("machine")
    machines = request.GET.get("machines")

    if bucket not in ["day", "hour"]:
        return Response(
            {
                "error": "bad_request",
                "reason": 'invalid value for bucket - must be "day" or "hour"',
            },
            status=400,
        )

    q = ~Q(reason__considered_downtime=False)

    start_dt = None
    if t_start:
        start_dt = dateutil.parser.isoparse(t_start)
        q = q & Q(end__gte=start_dt) | Q(end__isnull=True)

    end_dt = None
    if t_end:
        end_dt = dateutil.parser.isoparse(t_end)
        q = q & Q(start__lte=end_dt)

    if machine_id:
        q = q & Q(target__id__exact=machine_id)
    elif machines:
        machine_list = json.loads(machines)
        q = q & Q(target__id__in=machine_list)

    qs = State.objects.filter(q).order_by("start", "record_id")

    if start_dt is None:
        start_dt = qs.first().start

    end_dt = value_or_default_to_now(end_dt)

    windows = get_timestamp_windows(start_dt, end_dt, bucket)
    print(windows)

    output = get_windowed_downtime(qs, windows)

    return Response(output)


def get_timestamp_windows(start, end, bucket):
    if bucket == "hour":
        t_delta = datetime.timedelta(hours=1)
        t_start = start.replace(minute=0, second=0, microsecond=0)
    elif bucket == "day":
        t_delta = datetime.timedelta(days=1)
        t_start = start.replace(hour=0, minute=0, second=0, microsecond=0)

    windows = []
    t_cursor = t_start
    while t_cursor < end:
        t_next = t_cursor + t_delta
        windows.append({"start": t_cursor, "end": t_next})
        t_cursor = t_next

    return windows


def get_windowed_downtime(queryset, window_set):
    # window_set is a array of format [{"start":<datetime>,"end":<datetime>}]
    output = {}

    base_window_cursor = 0
    window_set_length = len(window_set)

    # pre-populate output
    machines_qs = (
        queryset.values("target", "target__name").order_by("target").distinct()
    )
    print(machines_qs)

    for entry in machines_qs:
        machine_id = entry["target"]
        machine_name = entry["target__name"]
        output[machine_id] = []
        for i in range(0, window_set_length):
            output[machine_id].append(
                {
                    "machine": str(machine_id),
                    "name": machine_name,
                    **window_set[i],
                    "running": 0,
                    "stopped": 0,
                    "count":0
                }
            )

    for state_entry in queryset:

        # fast forward window cursor to avoid unneccesary checking - only possible because state entries are ordered
        while (
            state_entry.start > window_set[base_window_cursor]["end"]
            and base_window_cursor < window_set_length
        ):
            base_window_cursor += 1

        for enum_cursor, window in enumerate(window_set[base_window_cursor:]):
            cursor = base_window_cursor + enum_cursor
            if state_entry.end and state_entry.end < window["start"]:
                break  # early exit

            # timestamp windowing
            end_ts = window_timestamp(
                value_or_default_to_now(state_entry.end),
                lower_limit=window["start"],
                upper_limit=window["end"],
            )
            start_ts = window_timestamp(
                state_entry.start,
                lower_limit=window["start"],
                upper_limit=window["end"],
            )

            # duration calculation
            duration = (end_ts - start_ts).total_seconds()
            print(
                f"<<{cursor}>>  {window['start']} ==:== {window['end']}  ({state_entry.start} {start_ts}) ({state_entry.end}  {end_ts}) {state_entry.running} {duration}"
            )
            if state_entry.running:
                output[state_entry.target.pk][cursor]["running"] += duration
            else:
                output[state_entry.target.pk][cursor]["stopped"] += duration
                output[state_entry.target.pk][cursor]["count"] += 1

    output = [
        {
            **item,
            "utilisation": (
                0
                if item["running"] == 0
                else item["running"] / (item["running"] + item["stopped"])
            ),
        }
        for value in output.values()
        for item in value
    ]

    return output


def value_or_default_to_now(timestamp):
    if timestamp is not None:
        return timestamp
    else:
        return datetime.datetime.now(tz=datetime.timezone.utc)


def window_timestamp(timestamp, upper_limit=None, lower_limit=None):
    windowed_ts = timestamp
    if lower_limit is not None and windowed_ts < lower_limit:
        windowed_ts = lower_limit

    if upper_limit is not None and windowed_ts > upper_limit:
        windowed_ts = upper_limit

    return windowed_ts


# def filter_window_set(start, end, window_set):
#     cursor = 0
#     window_set_length = len(window_set)

#     while start > window_set[cursor]["end"] and cursor < window_set_length:
#         cursor += 1

#     if cursor == window_set_length:
#         return []

#     start_cursor = cursor

#     if end is None:
#         end_cursor = window_set_length
#     else:
#         while end >= window_set[cursor]["start"] and cursor < window_set_length:
#             cursor += 1

#         end_cursor = cursor

#     return window_set[start_cursor:end_cursor]
