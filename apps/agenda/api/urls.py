"""
URLs de l'API agenda.
"""

from django.urls import path

from . import views

app_name = "agenda_api"

urlpatterns = [
    path("evenements/", views.EvenementListView.as_view(), name="evenements"),
    path("lieux/", views.LieuListView.as_view(), name="lieux"),
    path("lieux/geojson/", views.LieuxGeoJSONView.as_view(), name="lieux-geojson"),
]
