"""
Serializers pour l'API agenda.
"""

from rest_framework import serializers

from ..models import Categorie, Evenement, Lieu


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ["id", "nom", "slug", "couleur", "icone"]


class LieuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lieu
        fields = [
            "id",
            "nom",
            "slug",
            "adresse",
            "code_postal",
            "ville",
            "latitude",
            "longitude",
            "telephone",
            "site_web",
        ]


class EvenementSerializer(serializers.ModelSerializer):
    lieu = LieuSerializer(read_only=True)
    categorie = CategorieSerializer(read_only=True)
    
    class Meta:
        model = Evenement
        fields = [
            "id",
            "titre",
            "slug",
            "description",
            "date_debut",
            "date_fin",
            "heure_debut",
            "heure_fin",
            "lieu",
            "categorie",
            "prix",
            "url",
        ]
