from django.db.models import Q, F, Case, When, Value
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
def getAll(request):
    at = request.GET.get("t", None)
    page = int(request.GET.get("page", 0))
    page_length = request.GET.get("page-length", None)
    q = Q(end__isnull=True)

    if at:
        at_dt = dateutil.parser.isoparse(at)  # parse "at" to datetime
        q = (q | Q(end__gte=at_dt)) & Q(start__lte=at_dt)
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
def forMachine(request, machine_id):
    at = request.GET.get("t", None)

    q = Q(end__isnull=True)

    if at:
        at_dt = dateutil.parser.isoparse(at)  # parse "at" to datetime
        q = (q | Q(end__gte=at_dt)) & Q(start__lte=at_dt)
    q = q & Q(target__id__exact=machine_id)
    qs = State.objects.filter(q).order_by("-start").first()
    print(qs)
    serializer = StateSerializer(qs, many=False)
    return Response(serializer.data)


@api_view(("GET",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer, CSVRenderer))
def historyAll(request):
    t_start = request.GET.get("from", None)
    t_end = request.GET.get("to", None)
    running = request.GET.get("running", None)
    pretty = request.GET.get("pretty", False)
    page = int(request.GET.get("page", 0))
    page_length = request.GET.get("page-length", None)

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
def historyFor(request, machine_id=None):
    t_start = request.GET.get("from", None)
    t_end = request.GET.get("to", None)
    running = request.GET.get("running", None)
    pretty = request.GET.get("pretty", False)
    page = int(request.GET.get("page", 0))
    page_length = request.GET.get("page-length", None)

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
def downtimeForMachine(request, machine_id):
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

    q = q & Q(target__id__exact=machine_id)
    qs = State.objects.filter(q).order_by("-start")

    stopped_seconds = 0
    running_seconds = 0
    for entry in qs:
        end_ts = entry.end if entry.end is not None else datetime.datetime.now(tz=datetime.timezone.utc)
        if end_query_to_dt is not None and end_ts > end_query_to_dt:
            end_ts = end_query_to_dt

        start_ts = entry.start
        if start_query_from_dt is not None and start_ts < start_query_from_dt:
            start_ts = start_query_from_dt

        duration = (end_ts - start_ts).total_seconds()
        if entry.running:
            running_seconds += duration
        else:
            stopped_seconds += duration

    result = running_seconds / (running_seconds + stopped_seconds)
    return Response({"running":running_seconds,"stopped":stopped_seconds})
