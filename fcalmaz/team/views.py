from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404

from core.utils import DataMixin
from .models import Player


class Squad(DataMixin, ListView):
    template_name = 'team/squad.html'
    title_page = 'Состав команды'
    context_object_name = 'squad'

    def get_queryset(self):
        return Player.objects.all().order_by('pos')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        squad = self.get_queryset()
        return self.get_mixin_context(context, coaches=squad.filter(pos__name='Тренер'), goalkeepers=squad.filter(pos__name='Вратарь'),
                                      defenders=squad.filter(pos__name='Защитник'), midfielders=squad.filter(pos__name='Полузащитник'), forwards=squad.filter(pos__name='Нападающий'))


class PlayerInfo(DataMixin, DetailView):
    template_name = 'team/player.html'
    context_object_name = 'player'
    slug_url_kwarg = 'slug_player'

    def get_object(self, queryset = None):
        return get_object_or_404(Player.objects.all(), slug=self.kwargs[self.slug_url_kwarg])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(context, title=context['player'].name)