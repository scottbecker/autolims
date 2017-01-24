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


class TokenAuthentication(DefaultTokenAuthentication):
   

    def authenticate(self, request, *args, **kwargs):
        
        if request.META.get('HTTP_X_USER_TOKEN'):
            request.META['HTTP_AUTHORIZATION'] = 'Token %s'%request.META['HTTP_X_USER_TOKEN']
       

        return super(TokenAuthentication,self).authenticate(request, *args, **kwargs)
