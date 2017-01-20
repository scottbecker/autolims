from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, serializers
from serializers import UserSerializer, GroupSerializer
from django.http import HttpResponse
from django.views.generic.base import TemplateView, View
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.conf import settings
from django.core.urlresolvers import reverse

from models import Project, Organization, Run

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    
@login_required
def index(request):
    return HttpResponse("Hello world")

@method_decorator(login_required, name='dispatch')
class HomePageView(View):
    

    def dispatch(self, request):
        
        #get the users 
        
        organization_query = Organization.objects.filter(users=self.request.user)
        
        if not organization_query.exists():
            messages.add_message(self.request, messages.WARNING, 
                                 'User doesn\'t have any organizations')
            return redirect('%s?next=%s' % (settings.LOGIN_URL, self.request.path))            
        
        organization = organization_query.first()
        
        return redirect(reverse('projects', 
                                kwargs={'organization_subdomain':organization.subdomain}))

#class OrgAuthenticatingListView(ListView):
    

@method_decorator(login_required, name='dispatch')
class AuthenticatingView(View):
    
    def authenticate(self, request):
        return True
    
    def dispatch(self, *args, **kwargs):
        if not self.authenticate(self.request):
            return redirect('%s?next=%s' % (settings.LOGIN_URL, self.request.path))    
        return super(AuthenticatingView, self).dispatch(*args, **kwargs)  

class OrganizationAuthenticatingView(AuthenticatingView):

    def authenticate(self, request):
       
        valid_org = self.get_valid_current_org()
        
        if not valid_org:
            messages.add_message(self.request, messages.WARNING, 
                                 'doesn\'t exist or not allowed access to '
                                 'org with subdomain %s'%self.kwargs['organization_subdomain'])
            
            return False
        
        self.organization = valid_org
        
        return True
        
    
    def get_valid_current_org(self):
        
        org_query = Organization.objects.filter(subdomain=self.kwargs['organization_subdomain'])
        
        if not self.request.user.is_superuser: 
            org_query = org_query.filter(users=self.request.user)
        
        if not org_query.exists():
            return None
        
        return org_query.first()
    
    
        
class ProjectListView(OrganizationAuthenticatingView,ListView):
    model = Project
    template_name = 'projects.html'    
    
    def get_queryset(self):
        
        return Project.objects.filter(organization__subdomain=self.kwargs['organization_subdomain'])\
               .order_by('id')
    
    def get_context_data(self, *args, **kwargs):
        context_data = super(ProjectListView, self).get_context_data(*args, **kwargs)
        
        self.organization = Organization.objects.get(subdomain=self.kwargs['organization_subdomain'])
        context_data['organization_subdomain'] = self.kwargs['organization_subdomain']
        context_data['organization_name'] = self.organization.name
    
        return context_data    

class ProjectAuthenticatingView(OrganizationAuthenticatingView):
    def authenticate(self, request):
    
        if not super(ProjectAuthenticatingView, self).authenticate(request):
            return False
    
        project_query = Project.objects.filter(id=self.kwargs['project_id'],
                                               organization=self.organization)
    
    
    
        if not project_query.exists():
            messages.add_message(self.request, messages.WARNING, 
                                 'Invalid project/org combo')
    
            return False
    
        self.project = project_query.first()
    
        return True
    
class RunListView(ProjectAuthenticatingView, TemplateView):
    template_name = 'runs.html'    
    
  
        
    def get(self, request, *args, **kwargs):
        
        
        
        self.scheduled_runs = Run.objects.filter(project_id=self.kwargs['project_id'],
                                                 test_mode=False,
                                                 status__in=['accepted','in_progress']
                                                 )\
            .order_by('created_at')

        self.completed_runs = Run.objects.filter(project_id=self.kwargs['project_id'],
                                                 test_mode=False,
                                                 status__in = ['complete',
                                                               'aborted'])\
            .order_by('created_at')
        
        self.test_runs = Run.objects.filter(project_id=self.kwargs['project_id'],
                                         test_mode=True)\
            .order_by('created_at')
        
        self.canceled_runs = Run.objects.filter(project_id=self.kwargs['project_id'],
                                                status='canceled',
                                                test_mode=False)\
            .order_by('created_at')        

    
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)    
    

    def get_context_data(self, *args, **kwargs):
    
        context_data = super(RunListView, self).get_context_data(*args, **kwargs)    
    
        context_data.update({
            'sections': [
                {
                    'name':'Scheduled Runs',
                    'runs': self.scheduled_runs
                },
                {
                    'name':'Completed Runs',
                    'runs': self.completed_runs
                }, 
                {
                    'name':'Test Runs',
                    'runs': self.test_runs
                },
                {
                    'name':'Canceled Runs',
                    'runs': self.canceled_runs
                },                    
            ],
            'project': self.project,
        })
        
        return context_data    
    
class RunAuthenticatingView(ProjectAuthenticatingView):
    def authenticate(self, request):
    
        if not super(RunAuthenticatingView, self).authenticate(request):
            return False
    
        run_query = Run.objects.filter(id=self.kwargs['run_id'],
                                       project=self.project)
    
    
    
        if not run_query.exists():
            messages.add_message(self.request, messages.WARNING, 
                                 'Invalid run/project combo')
    
            return False
    
        self.run = run_query.first()
    
        return True    
    
    
class RunView(RunAuthenticatingView, TemplateView):
    template_name = 'run.html'    

    def get_context_data(self, *args, **kwargs):
    
        context_data = super(RunView, self).get_context_data(*args, **kwargs)    
    
        context_data.update({
            'run': self.run,
            'instructions': self.run.instructions.all().order_by('sequence_no'),
            'project': self.project,
        })
        
        return context_data   