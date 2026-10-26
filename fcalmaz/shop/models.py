from django.db import models
from django.conf import settings


class Product(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Цена"
    )
    rating = models.FloatField(default=0.0, verbose_name="Рейтинг")
    images = models.JSONField(
        default=list,
        verbose_name="Изображения (URLs)"
    )
    stock_quantity = models.PositiveIntegerField(
        default=0, 
        verbose_name="Количество на складе"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Позиция корзины"
        verbose_name_plural = "Позиции корзины"

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class PromoCode(models.Model):
    code = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Промокод"
    )
    discount_percentage = models.IntegerField(
        verbose_name="Скидка (%)"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"

    def __str__(self):
        return self.code