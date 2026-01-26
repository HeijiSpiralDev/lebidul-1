"""
Wagtail hooks pour l'application agenda.
"""

from wagtail import hooks

from .models import EvenementViewSet


@hooks.register("register_admin_viewset")
def register_evenement_viewset():
    """Enregistre le ViewSet Evenement dans l'admin Wagtail."""
    return EvenementViewSet()