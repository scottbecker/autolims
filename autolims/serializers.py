from django.contrib.auth.models import User, Group
from models import Run, Organization, Project
from rest_framework import serializers
from rest_framework.response import Response

from rest_framework.pagination import PageNumberPagination

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')
        
    
class RunSerializer(serializers.ModelSerializer):
    class Meta:
        model = Run
        fields = ('id','url', 'title', 'owner','project','protocol')
        
class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        depth=1
        fields = ('name', 'subdomain','projects')

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Run
        depth=0
        fields = ('id','title', 'status','projects')        
        
        
        
class PageNumberPaginationDataOnly(PageNumberPagination):
    # Set any other options you want here like page_size

    def get_paginated_response(self, data):
        return Response(data)