from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.urls import reverse
from django.template.defaultfilters import slugify
from django.contrib.auth import get_user_model

from team.models import translit_to_eng


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=Post.Status.PUBLISHED)


class Post(models.Model):
    class Status(models.IntegerChoices):
        DRAFT = 0, 'черновик'
        PUBLISHED = 1, 'опубликованно'
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="Slug")
    photo = models.ImageField(upload_to="post_photo/%y/%m/%d", default=None, blank=True, null=True, verbose_name="Фото")
    content = models.TextField(blank=True, verbose_name="Текст новости", validators=[MinLengthValidator(5, message="Минимум 5 символов"), MaxLengthValidator(10000, message="Максимум 10000 символов")])
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Время изменения")
    is_published = models.BooleanField(choices=tuple(map(lambda x: (bool(x[0]), x[1]), Status.choices)), default=Status.DRAFT, verbose_name="Статус")
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='posts', null=True, default=None) 

    objects = models.Manager()
    published = PublishedManager()

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('forum:post', kwargs={'post_slug': self.slug})
    
    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        date_slug = slugify(translit_to_eng(str(self.time_create)))
        title_slug = slugify(translit_to_eng(self.title))
        author_slug = slugify(translit_to_eng(self.author.username))

        self.slug = f'{title_slug}-{date_slug}-{author_slug}'
        super().save(*args, **kwargs) 


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name='Пост комментария', related_name='comments')
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, default=None) 
    content = models.TextField(blank=True, verbose_name="Текст новости", validators=[MinLengthValidator(5, message="Минимум 5 символов"), MaxLengthValidator(10000, message="Максимум 10000 символов")])                                   
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")

    def __str__(self):
        return f'Комментарий от {self.author.username} к посту "{self.post.title}"'

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"