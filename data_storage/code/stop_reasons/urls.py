from django.urls import path, include
from rest_framework import routers
from . import views
from django.shortcuts import redirect


def redirect_root(request):
    response = redirect("/admin")
    return response


urlpatterns = [
    path("list", views.listReasons),
    path("<uuid:machine_id>", views.getMachineReasons),
]
