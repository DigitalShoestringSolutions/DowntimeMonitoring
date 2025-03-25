from django.urls import path, include
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
    # path("downtime", views.downtime),
    # path("downtime/<uuid:machine_id>", views.downtime),
    path("downtime/machine", views.get_downtime_by_machine),
    path("downtime/machine/<uuid:machine_id>", views.get_downtime_by_machine),
    path("downtime/reasons", views.get_downtime_by_reason),
    path("downtime/reasons/<uuid:machine_id>", views.get_downtime_by_reason),
    path("downtime/category", views.get_downtime_by_category),
    path("downtime/category/<uuid:machine_id>", views.get_downtime_by_category),
    path("downtime/machine-reason", views.get_downtime_by_machine_reason),
    path(
        "downtime/machine-reason/<uuid:machine_id>",
        views.get_downtime_by_machine_reason,
    ),
    path("downtime/machine-category", views.get_downtime_by_machine_category),
    path(
        "downtime/machine-category/<uuid:machine_id>",
        views.get_downtime_by_machine_category,
    ),
    path("downtime/bucket", views.windowed_downtime),
]

# /state/                            ?t=timestamp
# /state/for/<machine_id>               ?t=timestamp
# /state/history                     ?from=timestamp ?to=timestamp
# /state/history/for/<machine_id>       ?from=timestamp ?to=timestamp
