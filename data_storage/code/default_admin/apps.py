from django.apps import AppConfig
from django.db.models.signals import post_migrate


class DefaultAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'default_admin'

    def ready(self):
        post_migrate.connect(create_default_admin,sender=self)


def create_default_admin(sender, **kwargs):
    from django.contrib.auth import get_user_model
    import os
    User = get_user_model()
    try:
        password = os.getenv("DEFAULT_ADMIN_PASSWORD")
        User.objects.create_superuser('admin','',password)
        print("Created default admin user")
    except:
        print("default admin not created - may already exist")
