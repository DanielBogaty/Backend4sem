from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from .models import Product, Cart, CartItem, PromoCode


class ProductCatalogTests(TestCase):

    """Тесты для каталога товаров: фильтрация, сортировка, валидация."""

    def setUp(self):
        cache.clear()
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

    def test_image_validation_requires_urls(self):
        """Каждое изображение должно быть http/https URL."""
        self.client.force_authenticate(user=self.admin)

        payload = {
            'title': 'Тестовый товар',
            'description': 'Описание',
            'price': 500,
            'rating': 4.0,
            'images': ['http://img1.jpg', 'not-a-url', 'http://img3.jpg'],
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

    def test_search_by_title(self):
        """Поиск по названию через параметр search."""
        resp = self.client.get(self.url, {'search': 'Бутсы'})
        data = resp.json()
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['title'], 'Бутсы Nike')

    def test_filter_by_min_rating(self):
        """Фильтрация по min_rating."""
        resp = self.client.get(self.url, {'min_rating': 4.5})
        data = resp.json()
        self.assertEqual(len(data['items']), 2)
        for item in data['items']:
            self.assertGreaterEqual(item['rating'], 4.5)

    def test_cache_invalidated_after_update(self):
        """После изменения товара каталог отдаёт свежие данные, а не кэш."""
        resp = self.client.get(self.url, {'sort_by': 'price'})
        self.assertEqual(resp.json()['items'][0]['title'], 'Щитки')

        self.client.force_authenticate(user=self.admin)
        product = Product.objects.get(title='Щитки')
        payload = {
            'title': 'Щитки',
            'description': 'Защитные щитки',
            'price': 99999.00,
            'rating': 3.2,
            'images': ['http://img1.jpg', 'http://img2.jpg', 'http://img3.jpg'],
        }
        patch = self.client.put(f'{self.url}{product.id}/', payload, format='json')
        self.assertEqual(patch.status_code, status.HTTP_200_OK)

        resp = self.client.get(self.url, {'sort_by': 'price'})
        self.assertEqual(resp.json()['items'][-1]['title'], 'Щитки')

class CartAndPromoTests(TestCase):
    """Тесты для корзины: добавление, остатки на складе, обновление, удаление и промокоды."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='cartuser',
            email='cart@example.com',
            password='testpassword123'
        )
        self.client.force_authenticate(user=self.user)

        self.product = Product.objects.create(
            title='Игровая футболка FC Almaz',
            description='Домашняя форма сезона',
            price=2500.00,
            stock_quantity=5,
            images=['http://img1.jpg', 'http://img2.jpg', 'http://img3.jpg'],
        )
        self.cart_url = '/api/cart/'
        self.items_url = '/api/cart/items/'
        self.promo_url = '/api/cart/apply-promo/'

    def test_get_empty_cart(self):
        """Получение пустой корзины авторизованного пользователя."""
        resp = self.client.get(self.cart_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data['items'], [])
        self.assertEqual(data['total_price'], '0.00')

    def test_unauthorized_access_denied(self):
        """Неавторизованный запрос к корзине возвращает 401."""
        anon_client = APIClient()
        resp = anon_client.get(self.cart_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_item_and_stock_validation(self):
        """Добавление товара в корзину, суммирование количества и проверка остатка."""
        # Успешное добавление 3 штук
        resp = self.client.post(
            self.items_url,
            {'product_id': self.product.id, 'quantity': 3},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.json()
        self.assertEqual(len(data['items']), 1)
        self.assertEqual(data['items'][0]['quantity'], 3)
        self.assertEqual(data['total_price'], '7500.00')

        # Попытка добавить ещё 3 штуки (итого 6 > 5 на складе) -> 400
        resp_over = self.client.post(
            self.items_url,
            {'product_id': self.product.id, 'quantity': 3},
            format='json'
        )
        self.assertEqual(resp_over.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', resp_over.json())

        # Нулевое или отрицательное количество -> 400
        resp_zero = self.client.post(
            self.items_url,
            {'product_id': self.product.id, 'quantity': 0},
            format='json'
        )
        self.assertEqual(resp_zero.status_code, status.HTTP_400_BAD_REQUEST)

        # Несуществующий товар -> 404
        resp_not_found = self.client.post(
            self.items_url,
            {'product_id': 999999, 'quantity': 1},
            format='json'
        )
        self.assertEqual(resp_not_found.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_and_remove_item_dynamic_total(self):
        """Обновление количества через PATCH, проверка остатка и удаление через DELETE."""
        add_resp = self.client.post(
            self.items_url,
            {'product_id': self.product.id, 'quantity': 2},
            format='json'
        )
        item_id = add_resp.json()['items'][0]['id']
        item_url = f'{self.items_url}{item_id}/'

        # Превышение остатка при PATCH -> 400
        patch_over = self.client.patch(item_url, {'quantity': 10}, format='json')
        self.assertEqual(patch_over.status_code, status.HTTP_400_BAD_REQUEST)

        # Корректное обновление до 4 штук -> 200 и пересчёт total_price (4 * 2500 = 10000.00)
        patch_ok = self.client.patch(item_url, {'quantity': 4}, format='json')
        self.assertEqual(patch_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_ok.json()['total_price'], '10000.00')

        # Удаление позиции -> 200 и обнуление total_price
        del_resp = self.client.delete(item_url)
        self.assertEqual(del_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(del_resp.json()['items'], [])
        self.assertEqual(del_resp.json()['total_price'], '0.00')

    def test_apply_promo_code(self):
        """Применение валидного и невалидного промокода к корзине."""
        self.client.post(
            self.items_url,
            {'product_id': self.product.id, 'quantity': 2},
            format='json'
        )

        # Валидный промокод SAVE10 (в нижнем регистре)
        resp = self.client.post(self.promo_url, {'code': 'save10'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data['promo_code'], 'SAVE10')
        self.assertEqual(data['discount_percentage'], 10)
        self.assertEqual(data['original_price'], '5000.00')
        self.assertEqual(data['discount_amount'], '500.00')
        self.assertEqual(data['final_price'], '4500.00')

        # Несуществующий промокод -> 400
        bad_resp = self.client.post(self.promo_url, {'code': 'FAKECODE'}, format='json')
        self.assertEqual(bad_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', bad_resp.json())

        # Неактивный промокод -> 400
        PromoCode.objects.create(code='OLD20', discount_percentage=20, is_active=False)
        inactive_resp = self.client.post(self.promo_url, {'code': 'OLD20'}, format='json')
        self.assertEqual(inactive_resp.status_code, status.HTTP_400_BAD_REQUEST)