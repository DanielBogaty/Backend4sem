from django.contrib import admin
from django.urls import path
from team import views

app_name = "team"

urlpatterns = [
    path('squad/', views.Squad.as_view(), name='squad'),
    path('player/<slug:slug_player>/', views.PlayerInfo.as_view(), name='player'),
]
