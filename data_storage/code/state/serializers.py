from rest_framework import serializers
from rest_framework.fields import UUIDField

from . import models


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Machine
        fields = ("id", "name", "sensor")


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.State
        fields = ("record_id", "target", "running", "start", "end", "reason")


class PrettyStateSerializer(serializers.ModelSerializer):
    target = serializers.SlugRelatedField(many=False, read_only=True, slug_field="name")
    reason = serializers.SlugRelatedField(many=False, read_only=True, slug_field="text")
    class Meta:
        model = models.State
        fields = ("record_id", "target", "running", "start", "end", "reason")

    def to_representation(self, instance):
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
    class Meta:
        model = models.StatusEvent
        fields = (
            "event_id",
            "item_id",
            "from_location_link",
            "to_location_link",
            "timestamp",
            "quantity",
        )
