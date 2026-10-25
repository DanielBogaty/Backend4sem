from django.urls import path
from core import views

urlpatterns = [
    path('', views.HomePage.as_view(), name='home'),
    path('news/<slug:news_slug>/', views.ShowNews.as_view(), name='news'),
    path('about/', views.AboutClub.as_view(), name='about'),
    path('contact/', views.ContactFormView.as_view(), name='contact')
]