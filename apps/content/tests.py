from datetime import date
from django.test import TestCase
from wagtail.models import Page, Site
from apps.content.models import (
    HomePage, BidulIndexPage, BidulPage,
    ArticleIndexPage, ArticlePage,
    LieuxIndexPage, LieuPage
)
from apps.agenda.models import Bidul, Lieu


class PageTreeMixin:
    @classmethod
    def setUpTestData(cls):
        root = Page.get_first_root_node()
        cls.home = root.add_child(instance=HomePage(
            title='Accueil', slug='accueil'
        ))
        Site.objects.all().delete()
        Site.objects.create(
            hostname='localhost', root_page=cls.home, is_default_site=True
        )
        cls.bidul_index = cls.home.add_child(instance=BidulIndexPage(
            title='Les Biduls', slug='biduls'
        ))
        cls.article_index = cls.home.add_child(instance=ArticleIndexPage(
            title='Chroniques', slug='chroniques'
        ))
        cls.lieux_index = cls.home.add_child(instance=LieuxIndexPage(
            title='Lieux', slug='lieux'
        ))
        cls.bidul = Bidul.objects.create(
            numero=311, mois=3, annee=2026,
            date_publication=date(2026, 3, 1)
        )
        cls.bidul_page = cls.bidul_index.add_child(instance=BidulPage(
            title='Le Bidul de mars 2026', slug='bidul-311', bidul=cls.bidul
        ))
        cls.article = cls.article_index.add_child(instance=ArticlePage(
            title='Article test', slug='article-test',
            date_publication=date(2026, 3, 15)
        ))
        cls.lieu = Lieu.objects.create(
            nom='L Oasis', slug='l-oasis',
            ville='Le Mans', code_postal='72000'
        )
        cls.lieu_page = cls.lieux_index.add_child(instance=LieuPage(
            title='L Oasis', slug='l-oasis-page', lieu=cls.lieu
        ))


class HomePageTest(PageTreeMixin, TestCase):
    def test_status_200(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_template(self):
        r = self.client.get('/')
        self.assertTemplateUsed(r, 'content/home_page.html')


class BidulIndexTest(PageTreeMixin, TestCase):
    def test_status_200(self):
        self.assertEqual(self.client.get('/biduls/').status_code, 200)

    def test_contains_bidul(self):
        self.assertContains(self.client.get('/biduls/'), '311')


class BidulPageTest(PageTreeMixin, TestCase):
    def test_status_200(self):
        self.assertEqual(self.client.get('/biduls/bidul-311/').status_code, 200)

    def test_bidul_linked(self):
        self.assertEqual(self.bidul_page.bidul.numero, 311)


class ArticleIndexTest(PageTreeMixin, TestCase):
    def test_status_200(self):
        self.assertEqual(self.client.get('/chroniques/').status_code, 200)

    def test_contains_article(self):
        self.assertContains(self.client.get('/chroniques/'), 'Article test')


class ArticlePageTest(PageTreeMixin, TestCase):
    def test_status_200(self):
        self.assertEqual(self.client.get('/chroniques/article-test/').status_code, 200)

    def test_date(self):
        self.assertEqual(self.article.date_publication, date(2026, 3, 15))


class LieuxIndexTest(PageTreeMixin, TestCase):
    def test_status_200(self):
        self.assertEqual(self.client.get('/lieux/').status_code, 200)


class LieuPageTest(PageTreeMixin, TestCase):
    def test_status_200(self):
        self.assertEqual(self.client.get('/lieux/l-oasis-page/').status_code, 200)

    def test_lieu_linked(self):
        self.assertEqual(self.lieu_page.lieu.nom, 'L Oasis')