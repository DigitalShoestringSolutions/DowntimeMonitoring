from django.db import models
import uuid


class Machine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=60)
    sensor = models.BooleanField(
        default=False,
        help_text="Set to true if running status is based on a sensor value",
    )

    def __str__(self):
        return self.name


class EventSource(models.TextChoices):
    SENSOR = "sensor", "Sensor"
    USER = "user", "User"


class StatusEvent(models.Model):
    event_id = models.BigAutoField(primary_key=True)
    target = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="event_records")
    running = models.BooleanField()
    timestamp = models.DateTimeField()

    source = models.CharField(max_length=6, choices=EventSource, null=True, blank=True)

    def __str__(self):
        return f"{self.target} - {self.running}"

    class Meta:
        verbose_name_plural = "Event Records"


class State(models.Model):
    record_id = models.BigAutoField(primary_key=True)
    target = models.ForeignKey(
        Machine, on_delete=models.CASCADE, related_name="state_records"
    )
    running = models.BooleanField()
    reason = models.ForeignKey(
        "stop_reasons.Reason", on_delete=models.SET_NULL, null=True, blank=True
    )
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)

    # links
    previous_entry = models.ForeignKey(
        "self",
        related_name="next_entry",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    trigger_event = models.ForeignKey(
        StatusEvent, related_name="resulting_state", on_delete=models.PROTECT
    )

    def __str__(self):
        return str(self.target)

    class Meta:
        verbose_name_plural = "State Records"
        indexes = [
            models.Index(fields=["-start", "-end"], name="timestamp_idx"),
        ]
