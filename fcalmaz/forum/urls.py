from django.urls import path
from forum import views

app_name = 'forum'

urlpatterns = [
    path('home/', views.ForumHome.as_view(), name='forum_home'),
    path('addpost/', views.AddPost.as_view(), name='add_post'),
    path('post/<slug:post_slug>/', views.ShowPost.as_view(), name='post'),
    path('post/<slug:post_slug>/addcomment/', views.AddComment.as_view(), name='add_comment'),
    path('edit/<slug:post_slug>/', views.EditPost.as_view(), name='edit_post'),
    path('delete/<slug:post_slug>/', views.DeletePost.as_view(), name='delete_post'),
    path('comment/<int:comment_id>/edit/', views.EditComment.as_view(), name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.DeleteComment.as_view(), name='delete_comment'),
]