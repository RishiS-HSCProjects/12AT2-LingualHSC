import bleach
from django import template

register = template.Library()

@register.filter(name='sanitise')
def sanitise(value):
    return bleach.clean(
        value, # Input text
        tags=["b", "i", "strong", "em", "p", "br"], # Allowed tags
        attributes={}, # No attributes allowed
        strip=True # Remove disallowed tags entirely
    )