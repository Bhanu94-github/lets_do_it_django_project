from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    """Safely gets a key from a dictionary."""
    try:
        return d.get(key, '')
    except Exception:
        return ''

@register.filter
def clean_token_label(value):
    """
    Converts a module token key like 'ai_module_1' to 'AI Module 1'.
    You can customize this logic as needed.
    """
    if not isinstance(value, str):
        return value
    return value.replace('_', ' ').title()
