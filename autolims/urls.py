from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.HomePageView.as_view(), name='home'),
    
    url(r'^(?P<org_subdomain>.*)/projects$', views.ProjectListView.as_view(), name='projects'),
    url(r'^(?P<org_subdomain>.*)/(?P<project_id>[0-9]+)/runs$', views.RunListView.as_view(), name='runs'),
    
    #url(r'^(?P<org_subdomain>.*)/$', views.HomePageView.as_view(), name='home'),
    
    #url(r'^(?P<page_slug>[\w-]+)-(?P<page_id>\w+)/history/$', views.history),
    #url(r'^(?P<page_slug>[\w-]+)-(?P<page_id>\w+)/edit/$', views.edit),
    #url(r'^(?P<page_slug>[\w-]+)-(?P<page_id>\w+)/discuss/$', views.discuss),
    #url(r'^(?P<page_slug>[\w-]+)-(?P<page_id>\w+)/permissions/$', views.permissions),
]