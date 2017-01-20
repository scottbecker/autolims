from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib.auth.views import logout
from . import views

urlpatterns = [
    url(r'^/?$', views.HomePageView.as_view(), name='home'),
    url(r'^logout/$', logout, {'next_page': '/login/'}),
    url(r'^(?P<organization_subdomain>.*)/projects$', 
        views.ProjectListView.as_view(), name='projects'),
    url(r'^(?P<organization_subdomain>.*)/(?P<project_id>[0-9]+)/runs$', 
        views.RunListView.as_view(), name='runs'),
    url(r'^(?P<organization_subdomain>.*)/(?P<project_id>[0-9]+)/runs/(?P<run_id>[0-9]+)$', 
        views.RunView.as_view(), name='run'),
     
    #url(r'^(?P<organization_subdomain>.*)/$', views.HomePageView.as_view(), name='home'),
    
    #url(r'^(?P<page_slug>[\w-]+)-(?P<page_id>\w+)/history/$', views.history),
    #url(r'^(?P<page_slug>[\w-]+)-(?P<page_id>\w+)/edit/$', views.edit),
    #url(r'^(?P<page_slug>[\w-]+)-(?P<page_id>\w+)/discuss/$', views.discuss),
    #url(r'^(?P<page_slug>[\w-]+)-(?P<page_id>\w+)/permissions/$', views.permissions),
]