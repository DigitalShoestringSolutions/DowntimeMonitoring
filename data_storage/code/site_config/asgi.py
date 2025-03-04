import os
from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'site_config.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
    }
)

import state_model.state_model
import shoestring_wrapper.wrapper


# shoestring_wrapper.wrapper.Wrapper.start({'zmq_config':zmq_config})
shoestring_wrapper.wrapper.MQTTServiceWrapper(
    settings.MQTT, settings.ZMQ_CONFIG
).start()
state_model_thread = state_model.state_model.StateModel(settings.ZMQ_CONFIG).start()
