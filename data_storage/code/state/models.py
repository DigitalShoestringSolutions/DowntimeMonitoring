from django.db import models
import uuid


class Machine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=60)
    
    enable_manual_input = models.BooleanField(
        default=True,
        help_text="If set to true, the machines status can be set manually in the user interface",
    )
    enable_historic_manual_input = models.BooleanField(
        default=False,
        help_text="If set to true, users can insert new downtime events into the history",
    )

    enable_edit_manual_input = models.BooleanField(
        default=True,
        help_text="If set to true, users can edit past events that were created manually",
    )
    enable_delete_manual_input = models.BooleanField(
        default=True,
        help_text="If set to true, users can delete past events that were created manually",
    )

    enable_edit_sensor_input = models.BooleanField(
        default=False,
        help_text="If set to true, users can edit past events that were created by sensor inputs",
    )
    enable_delete_sensor_input = models.BooleanField(
        default=False,
        help_text="If set to true, users can delete past events that were created by sensor inputs",
    )
    enable_historic_sensor_input = models.BooleanField(
        default=False,
        help_text="If set to true, sensor inputs with timestamps in the past (before the latest event) will be inserted, updating the history, if false they will be ignored",
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

    # links
    occured_during = models.ForeignKey("State",on_delete=models.SET_NULL,null=True,blank=True,related_name="events_during")
    next_entry = models.OneToOneField(
        "self",
        related_name="previous_entry",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"{self.event_id}: {self.target} - {self.running}"

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
    previous_entry = models.OneToOneField(
        "self",
        related_name="next_entry",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    trigger_event = models.OneToOneField(
        StatusEvent, related_name="resulting_state", on_delete=models.PROTECT
    )

    def __str__(self):
        return f"{self.record_id} - {str(self.target)}"

    class Meta:
        verbose_name_plural = "State Records"
        indexes = [
            models.Index(fields=["-start", "-end"], name="timestamp_idx"),
        ]
