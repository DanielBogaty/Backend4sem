from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.urls import reverse


class News(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="Slug")
    photo = models.ImageField(upload_to="news_photo/%y/%m/%d", default=None, blank=True, null=True, verbose_name="Фото")
    content = models.TextField(blank=True, verbose_name="Текст новости", validators=[MinLengthValidator(5, message="Минимум 5 символов"), MaxLengthValidator(10000, message="Максимум 10000 символов")])
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('news', kwargs={'news_slug': self.slug})
    
    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"