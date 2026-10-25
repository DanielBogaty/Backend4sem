from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, View, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse

from .models import Post, Comment
from .forms import AddPostForm, AddCommentForm
from core.utils import DataMixin
import fcalmaz.settings as settings


class ForumHome(DataMixin, ListView):
    template_name = 'forum/home.html'
    context_object_name = 'posts'
    title_page = 'Главная страница форума'

    def get_queryset(self):
        return Post.published.all().order_by('-time_update')
    

class AddPost(LoginRequiredMixin, CreateView):
    form_class = AddPostForm
    template_name = 'forum/addpost.html'
    title_page = 'Написать пост'

    def form_valid(self, form):
        w = form.save(commit=False)
        w.author = self.request.user
        return super().form_valid(form)
    

class ShowPost(DataMixin, DetailView):
    template_name = 'forum/post.html'
    context_object_name = 'post'
    slug_url_kwarg = 'post_slug'

    def get_object(self, queryset = None):
        return get_object_or_404(Post.objects.all(), slug=self.kwargs[self.slug_url_kwarg])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all().order_by('time_create')
        context['form_class'] = AddCommentForm()
        context['default_image'] = settings.DEFAULT_USER_IMAGE
        return self.get_mixin_context(context, title=context['post'].title)
    

class AddComment(LoginRequiredMixin, View):
    def post(self, request, post_slug):
        post = get_object_or_404(Post.published, slug=post_slug)
        form = AddCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
        return redirect('forum:post', post_slug=post.slug)


class EditPost(DataMixin, UpdateView):
    model = Post
    fields = ['title', 'content', 'photo', 'is_published']
    template_name = 'forum/addpost.html'
    title_page = "Редактирование поста"
    slug_url_kwarg = 'post_slug'
    slug_field = 'slug'

    def get_absolute_url(self):
        return reverse('forum:post', kwargs={'post_slug':self.object.slug})
    

class DeletePost(DataMixin, DeleteView):
    model = Post
    template_name = 'forum/delete_post.html'
    slug_url_kwarg = 'post_slug'
    slug_field = 'slug'

    def get_success_url(self):
        return reverse('forum:forum_home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(context, title = f'Удаление поста: {self.object.title}')
    

class EditComment(DataMixin, UpdateView):
    model = Comment
    form_class = AddCommentForm
    template_name = 'forum/edit_comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse('forum:post', kwargs={'post_slug': self.object.post.slug})
    

class DeleteComment(DataMixin, DeleteView):
    model = Comment
    template_name = 'forum/delete_comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse('forum:post', kwargs={'post_slug': self.object.post.slug})