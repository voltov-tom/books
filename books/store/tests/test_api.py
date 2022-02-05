import json

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from store.models import Book, UserBookRelation
from store.serializers import BookSerializer


class BooksApiTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_user')
        self.book1 = Book.objects.create(name='testbook1', price=30.50, author_name='good_author', owner=self.user)
        self.book2 = Book.objects.create(name='testbook2', price=229.50, author_name='bad_author')
        self.book3 = Book.objects.create(name='testbook3 bad_author', price=100.00, author_name='bad_author')
        self.book4 = Book.objects.create(name='testbook4', price=190.00, author_name='bad')

    def test_get(self):
        url = reverse('book-list')
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
            self.assertEqual(2, len(queries))
        # response = self.client.get(url)
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1)))).order_by('id')
        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)
        self.assertEqual(serializer_data[0]['rating'], None)

    def test_create(self):
        objects_before = Book.objects.all().count()
        url = reverse('book-list')
        data = {
            "name": "ProgPython 3",
            "price": 150,
            "author_name": "John"
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.post(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(objects_before + 1, Book.objects.all().count())
        self.assertEqual(self.user, Book.objects.last().owner)

    def test_update(self):
        url = reverse('book-detail', args=(self.book1.id,))
        data = {
            "name": self.book1.name,
            "price": 228,
            "author_name": self.book1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.put(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book1.refresh_from_db()
        self.assertEqual(228, self.book1.price)

    def test_delete(self):
        objects_before = Book.objects.all().count()
        url = reverse('book-detail', args=(self.book1.id,))
        self.client.force_login(self.user)
        response = self.client.delete(url)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(objects_before - 1, Book.objects.all().count())

    def test_search(self):
        url = reverse('book-list')
        books = Book.objects.filter(id__in=[self.book2.id, self.book3.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1)))).order_by('id')
        response = self.client.get(url, data={'search': 'bad_author'})
        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_sort(self):
        url = reverse('book-list')
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1)))).order_by('id')
        response = self.client.get(url, data={'ordering': 'price'})
        serializer_data = BookSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(sorted(serializer_data, key=lambda i: i['price'][2]), response.data)

    def test_update_not_owner(self):
        self.user2 = User.objects.create(username='test_user2')
        url = reverse('book-detail', args=(self.book1.id,))
        data = {
            "name": self.book1.name,
            "price": 228,
            "author_name": self.book1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.book1.refresh_from_db()
        self.assertEqual(30.50, self.book1.price)

    def test_delete_not_owner(self):
        self.user2 = User.objects.create(username='test_user2')
        objects_before = Book.objects.all().count()
        url = reverse('book-detail', args=(self.book1.id,))
        self.client.force_login(self.user2)
        response = self.client.delete(url)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(objects_before, Book.objects.all().count())

    def test_update_not_owner_but_staff(self):
        self.user2 = User.objects.create(username='test_user2', is_staff=True)
        url = reverse('book-detail', args=(self.book1.id,))
        data = {
            "name": self.book1.name,
            "price": 228,
            "author_name": self.book1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book1.refresh_from_db()
        self.assertEqual(228, self.book1.price)


class BooksRelationsApiTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='test_user')
        self.user2 = User.objects.create(username='test_user2')
        self.book1 = Book.objects.create(name='testbook1', price=30.50, author_name='good_author', owner=self.user1)
        self.book2 = Book.objects.create(name='testbook2', price=229.50, author_name='bad_author')

    def test_like(self):
        url = reverse('userbookrelation-detail', args=(self.book1.id,))
        data = {
            "like": True
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user1)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user1, book=self.book1)
        self.assertTrue(relation.like)

        # def test_in_bookmarks(self):
        #     url = reverse('userbookrelation-detail', args=(self.book1.id,))
        data = {
            "in_bookmarks": True
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user1)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user1, book=self.book1)
        self.assertTrue(relation.in_bookmarks)

    def test_rate(self):
        url = reverse('userbookrelation-detail', args=(self.book1.id,))
        data = {
            "rate": 4
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user1)
        response = self.client.patch(url, data=json_data, content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code, response.data)
        relation = UserBookRelation.objects.get(user=self.user1, book=self.book1)
        self.assertEqual(4, relation.rate)
