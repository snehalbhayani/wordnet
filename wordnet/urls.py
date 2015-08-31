from django.contrib.auth import authenticate
from django.conf.urls import patterns, include, url
from lookupword import views
from django.contrib import admin
import snippets
import activities
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'wordnet.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^form/', views.WordView),
    url(r'^lookup/', views.LookupWord),
    url(r'^', include('snippets.urls')),
    url(r'^', include('activities.urls')),
)
