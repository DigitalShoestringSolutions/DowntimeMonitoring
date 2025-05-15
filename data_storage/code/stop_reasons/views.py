from django.db.models import Q
from django.http import HttpResponse
from django.conf import settings
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

from . import models
from state import models as state_models
from . import serializers


@api_view(("GET",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer))
def listReasons(request):
    qs = models.Reason.objects.filter(considered_downtime=True)
    serializer = serializers.ReasonSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(("GET",))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer))
def getMachineReasons(request, machine_id):
    machine = state_models.Machine.objects.get(id=machine_id)
    reasons_qs = machine.reason_mapping.all()

    serializer = serializers.ReasonSerializer(reasons_qs, many=True)
    reasons = serializer.data  # [{"category":<>,"id":<>,"text":<>},...]

    category_reason_set = {}
    by_category_id = {}
    by_reason_id = {}
    for reason in reasons:
        key = reason["category"] if reason["category"] else "none"

        if category_reason_set.get(key) is None:
            category_reason_set[key] = []

            if key == "none":
                by_category_id[key] = {
                    "category_id": "none",
                    "category_name": "No Category",
                    "colour": "#DCDCDC",
                }
            else:
                category = models.Category.objects.get(pk=key)
                by_category_id[key] = {
                    "category_id": key,
                    "category_name": category.text,
                    "colour": category.colour,
                }

        category_reason_set[key].append(reason["id"])
        by_reason_id[reason["id"]] = reason

    for category_id in by_category_id.keys():
        by_category_id[category_id]["reasons"] = category_reason_set[category_id]

    return Response({"categories": by_category_id, "reasons": by_reason_id})
