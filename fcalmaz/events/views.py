from django.shortcuts import render
from django.views.generic import DetailView, ListView
from django.shortcuts import get_object_or_404

from core.utils import DataMixin
from .models import Match
import fcalmaz.settings as settings


class GamesShow(DataMixin, ListView):
    template_name = 'events/games.html'
    context_object_name = 'games'
    title_page = 'Игры'

    def get_queryset(self):
        return Match.played.all().order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(context, fcalmaz_logo=settings.DEFAULT_TEAM_IMAGE, default_logo=settings.DEFAULT_OPPONENT_IMAGE)


class ScheduleShow(DataMixin, ListView):
    template_name = 'events/schedule.html'
    context_object_name = 'games'
    title_page = 'Расписание'

    def get_queryset(self):
        return Match.not_played.all().order_by('date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(context, fcalmaz_logo=settings.DEFAULT_TEAM_IMAGE, default_logo=settings.DEFAULT_OPPONENT_IMAGE)
    
class MatchShow(DataMixin, DetailView):
    template_name = 'events/match.html'
    context_object_name = 'match'
    slug_url_kwarg = 'slug_match'

    def get_object(self, queryset = None):
        return get_object_or_404(Match.objects.all(), slug=self.kwargs[self.slug_url_kwarg])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(context, title=f"{context['match'].opponent} vs FC Almaz", fcalmaz_logo=settings.DEFAULT_TEAM_IMAGE, default_logo=settings.DEFAULT_OPPONENT_IMAGE)