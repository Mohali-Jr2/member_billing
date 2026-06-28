from django import template

register = template.Library()

@register.filter
def ugx(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 0
    return f"UGX {value:,}"
