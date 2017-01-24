from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib.auth.views import logout
from rest_framework import routers
from django.views.generic import RedirectView
from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'runs', views.RunViewSet)
router.register(r'organizations', views.OrganizationViewSet)

urlpatterns = [
    #----- API -----
    url(r'^api/', include(router.urls)),
    url(r'^api/(?P<organization_subdomain>[^/]*)/?$', 
        views.OrganizationFromNameView.as_view({'get':'get'}), name='organization_from_name_api'),    
    url(r'^api/(?P<organization_subdomain>[^/]*)/(?P<project_id>[0-9]+)/runs/?$', 
        views.ProjectFromOrganizationNameAPIView.as_view({"post":'create'}), name='project_from_organization_name_api'),          
        
    #redirect users that click the api output
    url(r'^api/(?P<organization_subdomain>[^/]*)/(?P<project_id>[0-9]+)/runs/(?P<run_id>[0-9]+)$', 
     RedirectView.as_view(url= '/%(organization_subdomain)s/%(project_id)s/runs/%(run_id)s')),
        
    #------Web-------
        
    url(r'^$', views.HomePageView.as_view(), name='home'),
    url(r'^logout/$', logout, {'next_page': '/login/'}),
    url(r'^(?P<organization_subdomain>[^/]*)/projects$', 
        views.ProjectListView.as_view(), name='projects'),
    url(r'^(?P<organization_subdomain>[^/]*)/containers/?$', 
        views.ContainerListView.as_view(), name='containers'),    
    
    #Run - list
    url(r'^(?P<organization_subdomain>[^/]*)/(?P<project_id>[0-9]+)/runs/?$', 
        views.RunListView.as_view(), name='runs'),
    #Run - View
    url(r'^(?P<organization_subdomain>[^/]*)/(?P<project_id>[0-9]+)/runs/(?P<run_id>[0-9]+)$', 
        views.RunView.as_view(), name='run'),
    #Run - execute 
    url(r'^(?P<organization_subdomain>[^/]*)/(?P<project_id>[0-9]+)/runs/(?P<run_id>[0-9]+)/execute/?$', 
        views.ExecuteRunView.as_view(), name='execute_run'),   
    #Run - cancel
    url(r'^(?P<organization_subdomain>[^/]*)/(?P<project_id>[0-9]+)/runs/(?P<run_id>[0-9]+)/cancel/?$', 
        views.CancelRunView.as_view(), name='cancel_r'),     
    #Run - abort
    url(r'^(?P<organization_subdomain>[^/]*)/(?P<project_id>[0-9]+)/runs/(?P<run_id>[0-9]+)/abort/?$', 
        views.AbortRunView.as_view(), name='abort_run'), 
    #Run - start progress
    url(r'^(?P<organization_subdomain>[^/]*)/(?P<project_id>[0-9]+)/runs/(?P<run_id>[0-9]+)/start_progress/?$', 
        views.StartProgressOnRunView.as_view(), name='start_progress_on_run'), 
    
    #Container - List
    url(r'^(?P<organization_subdomain>[^/]*)/containers/(?P<container_id>[0-9]+)$', 
        views.ContainerView.as_view(), name='container'),    

    
]