from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'role', 'is_staff', 'created_at')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    fieldsets = UserAdmin.fieldsets + (
        ('Роль и профиль', {
            'fields': ('role', 'photo', 'date_birth', 'created_at')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Роль и профиль', {
            'fields': ('role', 'email')
        }),
    )
