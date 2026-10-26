from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from django.db.models import Q

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


class ProductPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'limit'
    page_query_param = 'page'


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    filter_backends = [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ]
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'title', 'rating']

    def get_permissions(self):
        if self.action in ['destroy', 'create', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsAdminUser()]
        return [permissions.AllowAny()]

    def list(self, request, *args, **kwargs):
        # Кэширование запросов каталога
        cache_key = f"products_{request.GET.urlencode()}"
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
                    'total_items': queryset.count(),
                    'total_pages': self.paginator.page.paginator.num_pages,
                    'current_page': self.paginator.page.number,
                    'limit': self.paginator.get_page_size(request),
                }
            }
            
            # Сохраняем в кэш
            cache.set(cache_key, response_data, timeout=120)
            
            return self.get_paginated_response(response_data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        # Инвалидация кэша
        cache.clear()
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # Инвалидация кэша
        cache.clear()
        return response


class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_cart(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart

    def list(self, request):
        cart = self.get_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='items')
    def add_item(self, request):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Товар не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        cart = self.get_cart(request)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, item_id=None):
        cart = self.get_cart(request)
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Позиция не найдена'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        quantity = request.data.get('quantity')
        if quantity:
            item.quantity = quantity
            item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, item_id=None):
        cart = self.get_cart(request)
        
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Позиция не найдена'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='apply-promo')
    def apply_promo(self, request):
        serializer = ApplyPromoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        
        try:
            promo = PromoCode.objects.get(code=code, is_active=True)
        except PromoCode.DoesNotExist:
            return Response(
                {'error': 'Промокод недействителен'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        cart = self.get_cart(request)
        discount = cart.total_price * promo.discount_percentage / 100
        final_price = cart.total_price - discount

        return Response({
            'promo_code': promo.code,
            'discount_percentage': promo.discount_percentage,
            'original_price': cart.total_price,
            'discount_amount': discount,
            'final_price': final_price
        })