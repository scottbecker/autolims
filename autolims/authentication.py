"""
Provides various authentication policies.
"""
from __future__ import unicode_literals

import base64
import binascii

from django.contrib.auth import authenticate, get_user_model
from django.middleware.csrf import CsrfViewMiddleware
from django.utils.six import text_type
from django.utils.translation import ugettext_lazy as _

from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework.authentication import TokenAuthentication as DefaultTokenAuthentication

from django.contrib.auth import get_user_model

class TokenAuthentication(DefaultTokenAuthentication):
   

    def authenticate(self, request, *args, **kwargs):
        
        if request.META.get('HTTP_X_USER_TOKEN'):
            request.META['HTTP_AUTHORIZATION'] = 'Token %s'%request.META['HTTP_X_USER_TOKEN']
       

        return super(TokenAuthentication,self).authenticate(request, *args, **kwargs)

    
class EmailBackend(object):
    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        else:
            if getattr(user, 'is_active', False) and  user.check_password(password):
                return user
        return None
    
    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        