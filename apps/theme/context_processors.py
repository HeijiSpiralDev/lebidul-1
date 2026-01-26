"""
Context processors pour le thème.
"""


def theme_settings(request):
    """
    Injecte les paramètres de thème dans le contexte des templates.
    """
    from wagtail.models import Site
    
    from .models import ThemeSettings
    
    context = {
        "theme": None,
        "css_variables": {},
        "google_fonts_url": None,
    }
    
    try:
        site = Site.find_for_request(request)
        if site:
            theme = ThemeSettings.for_site(site)
            context["theme"] = theme
            context["css_variables"] = theme.css_variables
            context["google_fonts_url"] = theme.google_fonts_url
    except Exception:
        pass
    
    return context
