from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from .models import Product


class ProductCatalogTests(TestCase):
    """Тесты для каталога товаров: фильтрация, сортировка, валидация."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('shop:product-list')

        # создаём обычного пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # создаём админа
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )

        # товары для тестов
        Product.objects.create(
            title='Мяч футбольный',
            description='Официальный мяч',
            price=2500.00,
            rating=4.5,
            images=['http://img1.jpg', 'http://img2.jpg', 'http://img3.jpg'],
        )
        Product.objects.create(
            title='Бутсы Nike',
            description='Профессиональные бутсы',
            price=8900.00,
            rating=4.8,
            images=['http://img1.jpg', 'http://img2.jpg', 'http://img3.jpg'],
        )
        Product.objects.create(
            title='Щитки',
            description='Защитные щитки',
            price=1200.00,
            rating=3.2,
            images=['http://img1.jpg', 'http://img2.jpg', 'http://img3.jpg'],
        )

    def test_filter_by_price(self):
        """Фильтрация по min_price и max_price."""
        # min_price
        resp = self.client.get(self.url, {'min_price': 2000})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data['items']), 2)  # мяч и бутсы
        prices = [item['price'] for item in data['items']]
        for p in prices:
            self.assertGreaterEqual(float(p), 2000)

        # max_price
        resp = self.client.get(self.url, {'max_price': 1500})
        data = resp.json()
        self.assertEqual(len(data['items']), 1)  # только щитки
        self.assertEqual(data['items'][0]['title'], 'Щитки')

    def test_sort_by_price(self):
        """Сортировка по цене через sort_by и order."""
        # по возрастанию
        resp = self.client.get(self.url, {'sort_by': 'price', 'order': 'asc'})
        data = resp.json()
        prices = [float(item['price']) for item in data['items']]
        self.assertEqual(prices, sorted(prices))

        # по убыванию
        resp = self.client.get(self.url, {'sort_by': 'price', 'order': 'desc'})
        data = resp.json()
        prices = [float(item['price']) for item in data['items']]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_sort_by_title(self):
        """Сортировка по названию."""
        resp = self.client.get(self.url, {'sort_by': 'title', 'order': 'asc'})
        data = resp.json()
        titles = [item['title'] for item in data['items']]
        self.assertEqual(titles, sorted(titles))

    def test_image_validation_min_three(self):
        """Нельзя создать товар с меньше чем 3 изображениями."""
        self.client.force_authenticate(user=self.admin)

        payload = {
            'title': 'Тестовый товар',
            'description': 'Описание',
            'price': 500,
            'rating': 4.0,
            'images': ['http://img1.jpg', 'http://img2.jpg'],  # только 2
        }
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('images', resp.json())

    def test_pagination_format(self):
        """Проверяем формат ответа с items и meta."""
        resp = self.client.get(self.url, {'limit': 2})
        data = resp.json()
        self.assertIn('items', data)
        self.assertIn('meta', data)
        meta = data['meta']
        self.assertIn('total_items', meta)
        self.assertIn('total_pages', meta)
        self.assertIn('current_page', meta)
        self.assertIn('limit', meta)
        self.assertEqual(meta['limit'], 2)