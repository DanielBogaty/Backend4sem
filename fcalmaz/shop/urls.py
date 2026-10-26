from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'shop'

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
    path('cart/', views.CartViewSet.as_view({
        'get': 'list',
        'post': 'add_item'
    }), name='cart-list'),
    path('cart/items/<int:item_id>/', views.CartViewSet.as_view({
        'patch': 'update_item',
        'delete': 'remove_item'
    }), name='cart-item-detail'),
    path('cart/apply-promo/', views.CartViewSet.as_view({
        'post': 'apply_promo'
    }), name='cart-apply-promo'),
]