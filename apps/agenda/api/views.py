"""
Vues API pour l'agenda culturel.
"""

from django.utils import timezone

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Evenement, Lieu
from .serializers import EvenementSerializer, LieuSerializer


class EvenementListView(generics.ListAPIView):
    """Liste des événements avec filtres."""
    
    serializer_class = EvenementSerializer
    
    def get_queryset(self):
        queryset = Evenement.objects.filter(
            statut="publie"
        ).select_related("lieu", "categorie")
        
        # Filtres
        date_min = self.request.query_params.get("date_min")
        date_max = self.request.query_params.get("date_max")
        lieu_id = self.request.query_params.get("lieu")
        categorie_id = self.request.query_params.get("categorie")
        ville = self.request.query_params.get("ville")
        
        if date_min:
            queryset = queryset.filter(date_debut__gte=date_min)
        else:
            # Par défaut, événements à venir
            queryset = queryset.filter(date_debut__gte=timezone.now().date())
        
        if date_max:
            queryset = queryset.filter(date_debut__lte=date_max)
        
        if lieu_id:
            queryset = queryset.filter(lieu_id=lieu_id)
        
        if categorie_id:
            queryset = queryset.filter(categorie_id=categorie_id)
        
        if ville:
            queryset = queryset.filter(lieu__ville__icontains=ville)
        
        return queryset.order_by("date_debut", "heure_debut")


class LieuListView(generics.ListAPIView):
    """Liste des lieux."""
    
    serializer_class = LieuSerializer
    queryset = Lieu.objects.filter(actif=True)


class LieuxGeoJSONView(APIView):
    """Export GeoJSON des lieux pour Leaflet."""
    
    def get(self, request):
        lieux = Lieu.objects.filter(
            actif=True,
            latitude__isnull=False,
            longitude__isnull=False,
        )
        
        features = []
        for lieu in lieux:
            # Compter les événements à venir
            nb_events = Evenement.objects.filter(
                lieu=lieu,
                statut="publie",
                date_debut__gte=timezone.now().date(),
            ).count()
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lieu.longitude), float(lieu.latitude)],
                },
                "properties": {
                    "id": lieu.id,
                    "nom": lieu.nom,
                    "slug": lieu.slug,
                    "ville": lieu.ville,
                    "adresse": lieu.adresse_complete,
                    "nb_evenements": nb_events,
                },
            })
        
        return Response({
            "type": "FeatureCollection",
            "features": features,
        })
