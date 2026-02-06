from django import template

register = template.Library()

@register.filter
def underscore_to_space(value):
    """Replaces underscores with spaces."""
    if not value:
        return ""
    return value.replace("_", " ")
