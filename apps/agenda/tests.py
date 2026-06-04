from datetime import date
from django.test import TestCase
from apps.agenda.models import Bidul, Evenement, Lieu


class BidulModelTest(TestCase):
    def setUp(self):
        self.bidul = Bidul.objects.create(
            numero=1, mois=2, annee=1997,
            date_publication=date(1997, 2, 1),
            nb_evenements=42
        )

    def test_creation(self):
        self.assertEqual(self.bidul.numero, 1)
        self.assertEqual(self.bidul.annee, 1997)

    def test_str(self):
        self.assertIn(str(self.bidul.numero), str(self.bidul))

    def test_date_publication(self):
        self.assertEqual(self.bidul.date_publication, date(1997, 2, 1))


class LieuModelTest(TestCase):
    def setUp(self):
        self.lieu = Lieu.objects.create(
            nom='L Oasis', slug='l-oasis',
            ville='Le Mans', code_postal='72000', actif=True
        )

    def test_creation(self):
        self.assertEqual(self.lieu.nom, 'L Oasis')
        self.assertEqual(self.lieu.ville, 'Le Mans')

    def test_str(self):
        self.assertIn('Oasis', str(self.lieu))

    def test_slug(self):
        self.assertEqual(self.lieu.slug, 'l-oasis')


class EvenementModelTest(TestCase):
    def setUp(self):
        self.lieu = Lieu.objects.create(
            nom='Theatre', slug='theatre',
            ville='Le Mans', code_postal='72000'
        )
        self.evt = Evenement.objects.create(
            titre='Concert de jazz', slug='concert-jazz',
            date_debut=date(2026, 6, 15), lieu=self.lieu
        )

    def test_creation(self):
        self.assertEqual(self.evt.titre, 'Concert de jazz')

    def test_lieu_associe(self):
        self.assertEqual(self.evt.lieu.nom, 'Theatre')

    def test_str(self):
        self.assertIn('Concert', str(self.evt))