from django.shortcuts import render
from django.http import HttpResponseNotFound
from django.views.generic import ListView, DetailView, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.core.cache import cache

from .utils import DataMixin
from .models import News
from .forms import ContactForm


class HomePage(DataMixin, ListView):
    template_name = 'core/home.html'
    title_page = 'Главная страница'
    context_object_name = 'news'

    def get_queryset(self):
        n_lst = cache.get("news_posts")
        if not n_lst:
            n_lst = News.objects.all()
            cache.set("news_posts", n_lst, 60)
        return n_lst
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(context)


class ShowNews(DataMixin, DetailView):
    template_name = 'core/news.html'
    context_object_name = 'news'
    slug_url_kwarg = 'news_slug'

    def get_object(self, queryset = None):
        return get_object_or_404(News.objects.all(), slug=self.kwargs[self.slug_url_kwarg])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(context, title=context['news'].title)
    

class AboutClub(DataMixin, TemplateView):
    template_name = 'core/about.html'
    title_page = 'История клуба'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(context)
    

def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдена</h1>")


class ContactFormView(LoginRequiredMixin, DataMixin, FormView):
    template_name = 'core/contact.html'
    title_page = 'Контакты'
    form_class = ContactForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)