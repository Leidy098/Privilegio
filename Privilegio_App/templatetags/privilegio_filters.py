from django import template

register = template.Library()


@register.filter
def cop(value):
    try:
        return f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return value
