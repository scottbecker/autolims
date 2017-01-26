from django import template
from django.template.defaultfilters import stringfilter
import json

from autolims.models import Resource
from helper_funcs import str_respresents_int

register = template.Library()

def _to_safe_label(label):
    return label.replace(' ','_')


@register.filter( is_safe=True)
@stringfilter
def aliquot_to_container_label(value):
    """
    Covert an aliquot destination like 'plate 1/0' to plate_1
    """
    return _to_safe_label(value.split('/')[0])


@register.filter( is_safe=True)
@stringfilter
def to_safe_label(value):
    """
    Covert a label like 'plate 1' to plate_1
    """
    return _to_safe_label(value)


@register.filter(is_safe=True)
def format_json(d):
    """
    Covert a label like 'plate 1' to plate_1
    """
    return json.dumps(d)

@register.filter(is_safe=True)
def resource_id_to_name(resource_id):
    
    if isinstance(resource_id, basestring) and not str_respresents_int(resource_id):
        resource = Resource.objects.get(transcriptic_id=resource_id)
    else:
        resource = Resource.objects.get(id=resource_id)
        
    return resource.name