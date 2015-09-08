from django.contrib.auth import authenticate
from django.conf.urls import patterns, include, url
from django.contrib import admin

from rest_framework import routers
admin.autodiscover()

router = routers.SimpleRouter()
urlpatterns = router.urls
