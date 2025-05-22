from django.apps import AppConfig
from django.db.models.signals import post_migrate


class StopReasonsConfig(AppConfig):
    name = 'stop_reasons'

    def ready(self):
        post_migrate.connect(create_defaults, sender=self)


def create_defaults(sender, **kwargs):    
    from . import models
    if models.Reason.objects.all().count() == 0:
        ndt_category,_created = models.Category.objects.get_or_create(
            text="Not Downtime", defaults={"colour":models.CategoryColours.GREEN}
        )
        models.Category.objects.get_or_create(
            text="Planned", defaults={"colour": models.CategoryColours.BLUE}
        )
        models.Category.objects.get_or_create(
            text="Unplanned", defaults={"colour": models.CategoryColours.RED}
        )
        _, created = models.Reason.objects.get_or_create(
            text="End of Shift", defaults={"category": ndt_category,"considered_downtime":False}
        )
