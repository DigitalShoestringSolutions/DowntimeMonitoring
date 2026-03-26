from django.apps import AppConfig
from django.db.models.signals import post_migrate

class StateConfig(AppConfig):
    name = 'state'

    def ready(self):
        post_migrate.connect(create_defaults,sender=self)
        pass


def create_defaults(sender, **kwargs):
    from . import models
    print("Checking initial machine")
    if models.Machine.objects.all().count() == 0:
        models.Machine.objects.create(id="fdad651c-0c52-415d-bcdc-0dbc6d6f8d29", name="Machine 1")
        print("Created initial machine")
