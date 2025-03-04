from rest_framework import serializers
from rest_framework.fields import UUIDField

from . import models


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Machine
        fields = "__all__"


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.State
        fields = (
            "record_id",
            "target",
            "running",
            "start",
            "end",
            "reason",
        )


class PrettyStateSerializer(serializers.ModelSerializer):
    target = serializers.SlugRelatedField(many=False, read_only=True, slug_field="name")
    reason = serializers.SlugRelatedField(many=False, read_only=True, slug_field="text")
    class Meta:
        model = models.State
        fields = ("record_id", "target", "running", "start", "end", "reason")

    def to_representation(self, instance):
        context = self.context
        if context["wrap"]:
            if context["start"]:
                if instance.start<context["start"]:
                    instance.start = context["start"]

            if context["end"]:
                if instance.end is None or instance.end > context["end"]:
                    instance.end = context["end"]

        output = super().to_representation(instance)
        if output["reason"] is None:
            output["reason"] = "Running" if output["running"] else "Unspecified"

        return output


class MQTTStateSerializer(serializers.ModelSerializer):
    # required to coerce UUID into a string so that ZMQ's json library can handle
    target = serializers.PrimaryKeyRelatedField(
        read_only=True,
        allow_null=False,
        # This will properly serialize uuid.UUID to str:
        pk_field=UUIDField(format="hex_verbose"),
    )

    class Meta:
        model = models.State
        fields = ("record_id", "target", "running", "start", "end", "reason")


class EventSerializer(serializers.ModelSerializer):
    target = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = models.StatusEvent
        fields = ("event_id", "target", "running", "timestamp", "source")


class NestedStateSerialiser(serializers.ModelSerializer):
    class Meta:
        model = models.State
        fields = (
            "record_id",
            "target",
            "running",
            "start",
            "end",
            "reason"
        )

    def to_representation(self, instance):
        output = super().to_representation(instance)
        # remove filter to display ending event
        output["events_during"] = EventSerializer(
            instance.events_during.filter(running__exact=instance.running).order_by("-timestamp", "-event_id"), many=True
        ).data
        output["trigger_event"] = EventSerializer(instance.trigger_event, many=False).data
        return output

