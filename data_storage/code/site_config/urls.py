"""URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.shortcuts import redirect

def redirect_root(request):
    response = redirect('/admin')
    return response

urlpatterns = [
    path("/", redirect_root),
    path("admin/", admin.site.urls),
    path("state/", include("state.urls")),
    path("events/", include("state.event_urls")),
    path("machines/", include("state.machine_urls")),
    path("reasons/", include("stop_reasons.urls")),
]

admin.site.site_header = "Stop Reasons Admin"
admin.site.site_title = "Stop Reasons Admin Portal"
admin.site.index_title = "Welcome to Stop Reasons Administration Portal"

from django.contrib.auth.models import User, Group

admin.site.unregister(Group)
