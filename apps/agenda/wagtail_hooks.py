"""
Wagtail hooks pour l'application agenda.
"""

from wagtail import hooks
from wagtail.admin.menu import Menu, MenuItem, SubmenuMenuItem

from .models import EvenementViewSet


@hooks.register("register_admin_viewset")
def register_evenement_viewset():
    """Enregistre le ViewSet Evenement dans l'admin Wagtail."""
    return EvenementViewSet()

@hooks.register("register_admin_menu_item")
def register_agenda_menu():
    """Menu groupé pour l'agenda."""
    return SubmenuMenuItem(
        "Agenda",
        Menu(
            items=[
                MenuItem("Événements", "/admin/evenements/", icon_name="date", order=100),
                MenuItem("Lieux", "/admin/snippets/agenda/lieu/", icon_name="site", order=200),
                MenuItem("Catégories", "/admin/snippets/agenda/categorie/", icon_name="tag", order=300),
            ]
        ),
        icon_name="calendar",
        order=300,
    )