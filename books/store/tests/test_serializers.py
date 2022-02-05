from django.test import TestCase

from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg

from store.models import Book, UserBookRelation
from store.serializers import BookSerializer


class BookSerializersTestCase(TestCase):
    def test_ok(self):
        user1 = User.objects.create(username='user_1', first_name='ivan', last_name='petrov')
        user2 = User.objects.create(username='user_2', first_name='stas', last_name='timov')
        user3 = User.objects.create(username='user_3', first_name='gleb', last_name='byhoj')

        book1 = Book.objects.create(name='testbook1', price=25.55, author_name='bad_author', owner=user1)
        book2 = Book.objects.create(name='testbook2', price=22.55, author_name='bad_author')

        UserBookRelation.objects.create(user=user1, book=book2, like=True, rate=5)
        UserBookRelation.objects.create(user=user2, book=book2, like=True, rate=5)
        user_book_3 = UserBookRelation.objects.create(user=user3, book=book2, like=True)
        user_book_3.rate = 5
        user_book_3.save()

        UserBookRelation.objects.create(user=user1, book=book1, like=True, rate=3)
        UserBookRelation.objects.create(user=user2, book=book1, like=True, rate=4)
        UserBookRelation.objects.create(user=user3, book=book1, like=False)

        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1)))).order_by('id')
        data = BookSerializer(books, many=True).data
        expected_data = [
            {
                'id': book1.id,
                'name': 'testbook1',
                'price': '25.55',
                'author_name': 'bad_author',
                'annotated_likes': 2,
                'rating': '3.50',
                'owner_name': 'user_1',
                'readers': [
                    {
                        'first_name': 'ivan',
                        'last_name': 'petrov'
                    },
                    {
                        'first_name': 'stas',
                        'last_name': 'timov'
                    },
                    {
                        'first_name': 'gleb',
                        'last_name': 'byhoj'
                    }
                ]
            },
            {
                'id': book2.id,
                'name': 'testbook2',
                'price': '22.55',
                'author_name': 'bad_author',
                'annotated_likes': 3,
                'rating': '5.00',
                'owner_name': '',
                'readers': [
                    {
                        'first_name': 'ivan',
                        'last_name': 'petrov'
                    },
                    {
                        'first_name': 'stas',
                        'last_name': 'timov'
                    },
                    {
                        'first_name': 'gleb',
                        'last_name': 'byhoj'
                    }
                ]
            }
        ]
        # print(data)
        # print(expected_data)
        self.assertEqual(expected_data, data)
