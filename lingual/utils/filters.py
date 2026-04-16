"""
Adds filters for Jinja2 templates for more customisable rendering of content
"""

import bleach

def sanitise(value):
    """ Sanitises input to prevent XSS attacks, allowing only basic formatting tags. """
    return bleach.clean(
        value,
        tags=["b", "i", "strong", "em", "p", "br"],
        attributes={},
        strip=True
    )

def init_app(app):
    @app.template_filter("sanitise")
    def _sanitise_filter(value):
        return sanitise(value)
    
    return _sanitise_filter
