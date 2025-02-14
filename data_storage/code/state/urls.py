from django.urls import path,include
from rest_framework import routers
from . import views
# from django.shortcuts import redirect

# def redirect_root(request):
#     response = redirect('jobs/')
#     return response


urlpatterns = [
    path("", views.getAll),
    path("for/<str:machine_id>", views.forMachine),
    path("history", views.historyFor),
    path("history/for/<str:machine_id>", views.historyFor),
    path("set_reason/<int:record_id>", views.setReason),
    path("downtime/<str:machine_id>", views.downtimeForMachine),
]

# /state/                            ?t=timestamp
# /state/for/<machine_id>               ?t=timestamp
# /state/history                     ?from=timestamp ?to=timestamp
# /state/history/for/<machine_id>       ?from=timestamp ?to=timestamp
