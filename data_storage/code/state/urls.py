from django.urls import path,include
from rest_framework import routers
from . import views
# from django.shortcuts import redirect

# def redirect_root(request):
#     response = redirect('jobs/')
#     return response


urlpatterns = [
    path("", views.snapshot),
    path("<uuid:machine_id>", views.snapshot),
    path("history", views.history),
    path("history/<uuid:machine_id>", views.history),
    path("set_reason/<int:record_id>", views.setReason),
    path("downtime", views.downtime),
    path("downtime/<uuid:machine_id>", views.downtime),
    path("downtime/bucket", views.windowed_downtime),
]

# /state/                            ?t=timestamp
# /state/for/<machine_id>               ?t=timestamp
# /state/history                     ?from=timestamp ?to=timestamp
# /state/history/for/<machine_id>       ?from=timestamp ?to=timestamp
