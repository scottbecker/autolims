from django import template
from django.template.defaultfilters import stringfilter

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
