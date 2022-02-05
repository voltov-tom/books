from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from store.logic import set_rating
from store.models import Book, UserBookRelation


class SetRatingTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='user1', first_name='ivan', last_name='petrov')
        self.user2 = User.objects.create(username='user2', first_name='stas', last_name='timov')
        self.user3 = User.objects.create(username='user3', first_name='gleb', last_name='byhoj')

        self.book1 = Book.objects.create(name='testbook1', price=25.55, author_name='bad_author', owner=self.user1)

        UserBookRelation.objects.create(user=self.user1, book=self.book1, like=True, rate=3)
        UserBookRelation.objects.create(user=self.user2, book=self.book1, like=True, rate=4)
        UserBookRelation.objects.create(user=self.user3, book=self.book1, like=False)

    def test_ok(self):
        set_rating(self.book1)
        self.book1.refresh_from_db()
        self.assertEqual('3.50', str(self.book1.rating))
