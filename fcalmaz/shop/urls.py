from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from . import views

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
    path('api/', include('shop.urls')),
    path('api/auth/register', views.RegisterView.as_view(), name='register'),
    path('api/auth/login', views.LoginView.as_view(), name='login'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]