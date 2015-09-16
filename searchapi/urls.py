from django.contrib.auth import authenticate
from django.conf.urls import patterns, include, url
from django.contrib import admin
from views import SearchViewSet, HelpViewSet
from rest_framework import routers

router = routers.SimpleRouter()
# Here we register all views for looking up various details about words using wordnet apis. 
#router.register(r'v1/wordnet/(?P<arg1>.+)/(?P<arg2>.+)/(?P<arg3>(.*))', LookupWordViewSet,base_name='wordnet')
router.register(r'v1/search', SearchViewSet,base_name='search_relation')
router.register(r'v1/search/help', HelpViewSet,base_name='search_APIdetails')
urlpatterns = router.urls
