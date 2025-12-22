from django import template

register = template.Library()

@register.filter
def getattr_custom(obj, attr_name):
    """Safely get attribute from object in template"""
    return getattr(obj, attr_name, None)

@register.filter
def zip(a, b):
    return zip(a, b)