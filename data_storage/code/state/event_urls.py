from django.urls import path,include
from rest_framework import routers
from . import views
# from django.shortcuts import redirect

# def redirect_root(request):
#     response = redirect('jobs/')
#     return response


urlpatterns = [
    path("<uuid:machine_id>", views.eventsForMachine),
    path("by-state/<uuid:machine_id>", views.eventsForMachineByState),
    path("update/<int:event_id>", views.updateEvent),
    path("delete/<int:event_id>", views.deleteEvent),
]

# /events/                           ?from=timestamp ?to=timestamp
# /events/for/<item_id>              ?from=timestamp ?to=timestamp
# /events/to/<loc_id>                ?from=timestamp ?to=timestamp
# /events/from/<loc_id>              ?from=timestamp ?to=timestamp
# /events/at/<loc_id>                ?from=timestamp ?to=timestamp
