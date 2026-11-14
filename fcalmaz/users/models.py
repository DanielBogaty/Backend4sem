from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Покупатель'
        ADMIN = 'admin', 'Администратор'

    email = models.EmailField(
        unique=True,
        verbose_name='Email'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата регистрации'
    )

    photo = models.ImageField(
        upload_to='user_photo/%Y/%m/%d',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    date_birth = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Дата рождения'
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name='Роль'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"