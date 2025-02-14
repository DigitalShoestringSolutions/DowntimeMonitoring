from django.contrib import admin
from . import models
# from adminsortable.admin import SortableAdmin
from stop_reasons.admin import MachineReasonMapInline


@admin.register(models.Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("name", "sensor")
    fields = ("id", "name", "sensor")
    readonly_fields = ("id",)
    inlines = (MachineReasonMapInline,)


@admin.register(models.State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['record_id','target','running','start','end','reason']
    fields = ("record_id", "target", "running", "start", "end", "reason")
    readonly_fields = ('record_id',)
    list_filter = ["target","running","reason"]
    ordering = ["-start"]

@admin.register(models.StatusEvent)
class EventAdmin(admin.ModelAdmin):
    list_display = ['event_id','target','running','timestamp','source']
    fields = ("event_id", "target", "running", "timestamp", "source")
    readonly_fields = ('event_id',)
    list_filter = ["target","running","source"]
    ordering = ["timestamp"]
    
