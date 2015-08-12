from django.contrib.auth import authenticate
from django.conf.urls import patterns, include, url
from django.contrib import admin
from views import LookupWordViewSet, LookupWordRelationViewSet, HelpViewSet
from rest_framework import routers

router = routers.SimpleRouter()
# Here we register all views for looking up various details about words using wordnet apis. 
#router.register(r'v1/wordnet/(?P<arg1>.+)/(?P<arg2>.+)/(?P<arg3>(.*))', LookupWordViewSet,base_name='wordnet')
router.register(r'v1/wordnet/(?P<arg1>.+)/(?P<arg2>.+)/(?P<arg3>.+)', LookupWordRelationViewSet,base_name='findrelation')
router.register(r'v1/wordnet/(?P<arg1>.+)/(?P<arg2>.+)', LookupWordViewSet,base_name='lookupword')
router.register(r'v1/wordnet/help', HelpViewSet,base_name='API')
urlpatterns = router.urls
