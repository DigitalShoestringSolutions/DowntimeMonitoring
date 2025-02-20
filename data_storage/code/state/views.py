from django.db.models import Q, F, Case, When, Value, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.paginator import Paginator
from rest_framework import viewsets, status
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

from .models import State, StatusEvent, Machine
from stop_reasons.models import Reason
from .serializers import (
    StateSerializer,
    EventSerializer,
    MachineSerializer,
    MQTTStateSerializer,
    PrettyStateSerializer,
)
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

    qs = State.objects.filter(q).order_by("-start")

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
    page = int(request.GET.get("page", 0))
    page_length = request.GET.get("page-length", None)
    duration_str = request.GET.get("duration", None)

    q = Q()

    serializer_class = PrettyStateSerializer if pretty == "true" else StateSerializer

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

    if duration_str:
        try:
            duration = float(duration_str)
            q = q & (
                Q(end__gte=F("start") + datetime.timedelta(minutes=duration))
                | Q(end__isnull=True)
            )
        except ValueError:
            pass  # duration was not valid - ignore

    qs = State.objects.filter(q).order_by("-start")
    if page_length:
        paginator = Paginator(qs, page_length)
        try:
            qs_slice = paginator.page(page if page > 0 else 1)
        except:
            qs_slice = []
        serializer = serializer_class(qs_slice, many=True)
    else:
        serializer = serializer_class(qs, many=True)
    return Response(serializer.data)


@api_view(("GET",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer, CSVRenderer))
def getAllEvents(request):
    t_start = request.GET.get("from", None)
    t_end = request.GET.get("to", None)
    print(f"all events {t_start}>{t_end}")

    q = Q()

    if t_start:
        start_dt = dateutil.parser.isoparse(t_start)
        q = q & Q(timestamp__gte=start_dt)

    if t_end:
        end_dt = dateutil.parser.isoparse(t_end)
        q = q & Q(timestamp__lte=end_dt)

    qs = Event.objects.filter(q).order_by("-timestamp")
    serializer = EventSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(("GET",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer, CSVRenderer))
def eventsForItem(request, item_id):
    t_start = request.GET.get("from", None)
    t_end = request.GET.get("to", None)
    print(f"all events {t_start}>{t_end}")

    q = Q(item_id__exact=item_id)

    if t_start:
        start_dt = dateutil.parser.isoparse(t_start)
        q = q & Q(timestamp__gte=start_dt)

    if t_end:
        end_dt = dateutil.parser.isoparse(t_end)
        q = q & Q(timestamp__lte=end_dt)

    qs = Event.objects.filter(q).order_by("-timestamp")
    serializer = EventSerializer(qs, many=True)
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

    qs = State.objects.filter(q).order_by("-start")

    machine_results = {}
    reason_results = {}
    machine_reason_results = {}
    for entry in qs:
        # output init
        if entry.target not in machine_results:
            machine_results[entry.target] = {"running": 0, "stopped": 0, "count": 0}
            machine_reason_results[entry.target] = {}

        # timestamp windowing
        end_ts = (
            entry.end
            if entry.end is not None
            else datetime.datetime.now(tz=datetime.timezone.utc)
        )
        if end_query_to_dt is not None and end_ts > end_query_to_dt:
            end_ts = end_query_to_dt

        start_ts = entry.start
        if start_query_from_dt is not None and start_ts < start_query_from_dt:
            start_ts = start_query_from_dt

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
