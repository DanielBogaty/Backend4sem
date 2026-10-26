from django.contrib import admin
from .models import Product, Cart, CartItem, PromoCode


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'rating', 'stock_quantity', 'created_at')
    list_filter = ('created_at', 'stock_quantity')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    list_editable = ()


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity')


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code',)