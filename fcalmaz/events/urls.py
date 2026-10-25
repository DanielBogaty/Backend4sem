from django.contrib import admin
from django.urls import path
from events import views

app_name = "events"

urlpatterns = [
    path('games/', views.GamesShow.as_view(), name='games'),
    path('schedule/', views.ScheduleShow.as_view(), name='schedule'),
    path('match/<slug:slug_match>/', views.MatchShow.as_view(), name='match')
]
