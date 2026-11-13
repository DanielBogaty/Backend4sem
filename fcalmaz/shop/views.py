from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from drf_spectacular.utils import extend_schema, OpenApiTypes, OpenApiParameter, OpenApiExample
from drf_spectacular.utils import inline_serializer
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from decimal import Decimal, ROUND_HALF_UP
from .models import Product, Cart, CartItem, PromoCode
from .serializers import (
    ProductSerializer, CartSerializer, CartItemSerializer,
    PromoCodeSerializer, ApplyPromoSerializer
)


class IsAdminUser(permissions.BasePermission):
    """Разрешение только для администраторов"""

    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'


class IsCustomerUser(permissions.BasePermission):
    """Разрешение только для покупателей"""

    def has_permission(self, request, view):
        return request.user and request.user.role == 'customer'


CATALOG_VERSION_KEY = 'products_version'


def invalidate_catalog_cache():
    cache.set(CATALOG_VERSION_KEY, cache.get(
        CATALOG_VERSION_KEY, 0) + 1, timeout=None)


class ProductPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'limit'
    page_query_param = 'page'


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'title', 'rating']

    def get_permissions(self):
        if self.action in ['destroy', 'create', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsAdminUser()]
        return [permissions.AllowAny()]

    def filter_queryset(self, queryset):
        # кастомная сортировка через sort_by и order
        sort_by = self.request.query_params.get('sort_by')
        order = self.request.query_params.get('order', 'asc')

        if sort_by in ['price', 'title']:
            if order == 'desc':
                sort_by = '-' + sort_by
            queryset = queryset.order_by(sort_by)

        return super().filter_queryset(queryset)

    @extend_schema(
        summary='Список товаров',
        description='Каталог товаров с пагинацией, фильтрацией и сортировкой.',
        parameters=[
            OpenApiParameter(name='search', type=str,
                             description='Поиск по названию/описанию'),
            OpenApiParameter(name='min_price', type=float,
                             description='Мин. цена'),
            OpenApiParameter(name='max_price', type=float,
                             description='Макс. цена'),
            OpenApiParameter(name='min_rating', type=float,
                             description='Мин. рейтинг'),
            OpenApiParameter(name='sort_by', type=str,
                             description='Поле сортировки (price/title)'),
            OpenApiParameter(name='order', type=str,
                             description='Порядок (asc/desc)'),
            OpenApiParameter(name='page', type=int,
                             description='Номер страницы'),
            OpenApiParameter(name='limit', type=int,
                             description='Элементов на странице'),
        ],
    )
    def list(self, request, *args, **kwargs):
        # Кэширование запросов каталога
        version = cache.get(CATALOG_VERSION_KEY, 0)
        cache_key = f"products_v{version}_{request.GET.urlencode()}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # Фильтрация
        queryset = self.filter_queryset(self.get_queryset())

        # Фильтр по цене
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Фильтр по рейтингу
        min_rating = request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)

        # Пагинация
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = {
                'items': serializer.data,
                'meta': {
                    'total_items': self.paginator.page.paginator.count,
                    'total_pages': self.paginator.page.paginator.num_pages,
                    'current_page': self.paginator.page.number,
                    'limit': self.paginator.get_page_size(request),
                }
            }

            # Сохраняем в кэш
            cache.set(cache_key, response_data, timeout=120)

            return Response(response_data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Получить товар',
        description='Детальная информация о товаре по ID.',
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Создать товар',
        description='Создание нового товара (только admin).',
    )
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        invalidate_catalog_cache()
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        invalidate_catalog_cache()
        return response

    @extend_schema(
        summary='Удалить товар',
        description='Удаление товара по ID (только admin).',
    )
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        invalidate_catalog_cache()
        return response


class EmptySerializer(serializers.Serializer):
    pass


@extend_schema(tags=['cart'])
class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_cart(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart

    @extend_schema(
        summary="Получить корзину",
        description="Возвращает текущую корзину авторизованного пользователя со списком позиций и общей суммой.",
        responses={200: CartSerializer},
    )
    def list(self, request):
        cart = self.get_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @extend_schema(
        summary="Добавить товар в корзину",
        description="Добавляет товар в корзину с проверкой остатков на складе (stock_quantity).",
        request=inline_serializer(
            name='AddCartItemRequest',
            fields={
                'product_id': serializers.IntegerField(),
                'quantity': serializers.IntegerField(required=False, default=1),
            }
        ),
        responses={
            201: CartSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=False, methods=['post'], url_path='items')
    def add_item(self, request):
        product_id = request.data.get('product_id')
        try:
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response(
                {'error': 'Количество должно быть целым числом'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity <= 0:
            return Response(
                {'error': 'Количество должно быть больше нуля'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Товар не найден'}, status=status.HTTP_404_NOT_FOUND)

        cart = self.get_cart(request)
        existing_item = CartItem.objects.filter(
            cart=cart, product=product).first()
        current_in_cart = existing_item.quantity if existing_item else 0

        if current_in_cart + quantity > product.stock_quantity:
            return Response(
                {
                    'error': f'Недостаточно товара на складе. Доступно: {product.stock_quantity}, в корзине уже: {current_in_cart}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if existing_item:
            existing_item.quantity += quantity
            existing_item.save()
        else:
            CartItem.objects.create(
                cart=cart, product=product, quantity=quantity)

        cart.refresh_from_db()
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Изменить количество товара в корзине",
        description="Обновляет количество позиции в корзине с проверкой остатков и динамическим пересчётом total_price.",
        request=inline_serializer(
            name='UpdateCartItemRequest',
            fields={
                'quantity': serializers.IntegerField(),
            }
        ),
        responses={
            200: CartSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=False, methods=['patch'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, item_id=None):
        cart = self.get_cart(request)
        try:
            item = CartItem.objects.select_related(
                'product').get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'error': 'Позиция не найдена'}, status=status.HTTP_404_NOT_FOUND)

        try:
            quantity = int(request.data.get('quantity'))
        except (TypeError, ValueError):
            return Response(
                {'error': 'Укажите корректное количество'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity <= 0:
            return Response(
                {'error': 'Количество должно быть больше нуля'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity > item.product.stock_quantity:
            return Response(
                {'error': f'Превышен остаток на складе (доступно: {item.product.stock_quantity})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        item.quantity = quantity
        item.save()

        cart.refresh_from_db()
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @extend_schema(
        summary="Удалить товар из корзины",
        description="Удаляет выбранную позицию из корзины и пересчитывает total_price.",
        responses={
            200: CartSerializer,
            404: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=False, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, item_id=None):
        cart = self.get_cart(request)
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
        except CartItem.DoesNotExist:
            return Response({'error': 'Позиция не найдена'}, status=status.HTTP_404_NOT_FOUND)

        cart.refresh_from_db()
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @extend_schema(
        summary="Применить промокод к корзине",
        description="Проверяет активность промокода (например, SAVE10) и рассчитывает итоговую сумму со скидкой.",
        request=ApplyPromoSerializer,
        responses={
            200: inline_serializer(
                name='ApplyPromoResponse',
                fields={
                    'promo_code': serializers.CharField(),
                    'discount_percentage': serializers.IntegerField(),
                    'original_price': serializers.CharField(),
                    'discount_amount': serializers.CharField(),
                    'final_price': serializers.CharField(),
                }
            ),
            400: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=False, methods=['post'], url_path='apply-promo')
    def apply_promo(self, request):
        serializer = ApplyPromoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code'].strip().upper()

        PromoCode.objects.get_or_create(
            code='SAVE10',
            defaults={'discount_percentage': 10, 'is_active': True}
        )

        try:
            promo = PromoCode.objects.get(code__iexact=code, is_active=True)
        except PromoCode.DoesNotExist:
            return Response(
                {'error': 'Промокод не найден или неактивен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = self.get_cart(request)
        original_price = Decimal(cart.total_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        discount_amount = (original_price * Decimal(promo.discount_percentage) / Decimal('100')).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        final_price = (original_price - discount_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return Response({
            'promo_code': promo.code,
            'discount_percentage': promo.discount_percentage,
            'original_price': f"{original_price:.2f}",
            'discount_amount': f"{discount_amount:.2f}",
            'final_price': f"{final_price:.2f}",
        }, status=status.HTTP_200_OK)

class CatalogPageView(TemplateView):
    """Страница каталога товаров."""
    template_name = 'shop/catalog.html'
    extra_context = {'title': 'Каталог товаров'}

class CartPageView(LoginRequiredMixin, TemplateView):
    """Страница корзины покупок."""
    template_name = 'shop/cart.html'
    extra_context = {'title': 'Корзина'}
