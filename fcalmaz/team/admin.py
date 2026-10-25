from django.contrib import admin
from .models import Position, Player


class PlayerAdmin(admin.ModelAdmin):
    readonly_fields = ('slug', )

admin.site.register(Position)
admin.site.register(Player, PlayerAdmin)