from django.apps import AppConfig
from django.db.models.signals import post_migrate


class StopReasonsConfig(AppConfig):
    name = 'stop_reasons'

    def ready(self):
        post_migrate.connect(create_default_admin, sender=self)


def create_default_admin(sender, **kwargs):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        User.objects.create_superuser('admin','','admin')
        print("Created default admin user")
    except:
        print("default admin not created - may already exist")
