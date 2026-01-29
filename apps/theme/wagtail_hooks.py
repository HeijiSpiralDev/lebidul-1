"""
Personnalisation de l'admin Wagtail pour Le Bidul.
"""

from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks


@hooks.register("insert_global_admin_css")
def global_admin_css():
    """CSS personnalisé pour l'admin."""
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static("css/admin/custom.css")
    )


@hooks.register("insert_global_admin_js")
def global_admin_js():
    """JS personnalisé pour l'admin (optionnel)."""
    return format_html(
        '<script src="{}"></script>',
        static("js/admin/custom.js")
    )