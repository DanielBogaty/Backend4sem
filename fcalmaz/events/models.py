from django.db import models
from django.urls import reverse
from team.models import translit_to_eng
from django.template.defaultfilters import slugify


class PlayedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_future=Match.StatusFuture.PLAYED)
    
class NotPlayedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_future=Match.StatusFuture.NOT_PLAYED)


class Match(models.Model):
    class StatusHome(models.IntegerChoices):
        GUEST = 0, 'гостевая игра'
        HOME = 1, 'домашняя игра'

    class StatusFuture(models.IntegerChoices):
        NOT_PLAYED = 0, 'не сыгранна'
        PLAYED = 1, 'сыгранна'
    
    opponent = models.CharField(max_length=255, verbose_name='Противник')
    logo = models.ImageField(upload_to="team_photo/%y/%m/%d", default=None, blank=True, null=True, verbose_name="Лого")
    date = models.DateField(verbose_name='Дата')
    time = models.TimeField(blank=True, null=True, verbose_name='Время')
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="Slug")
    score = models.CharField(max_length=10, blank=True, null=True, verbose_name='Счёт')
    is_home = models.BooleanField(choices=tuple(map(lambda x: (bool(x[0]), x[1]), StatusHome.choices)), default=StatusHome.HOME, verbose_name='Расположение')
    is_future = models.BooleanField(choices=tuple(map(lambda x: (bool(x[0]), x[1]), StatusFuture.choices)), default=StatusFuture.NOT_PLAYED, verbose_name='Статус')

    objects = models.Manager()
    played = PlayedManager()
    not_played = NotPlayedManager()

    def __str__(self):
        return f"{self.opponent} - {self.date}"
    
    def get_absolute_url(self):
        return reverse('events:match', kwargs={'slug_match': self.slug})
    
    class Meta:
        verbose_name = "Матч"
        verbose_name_plural = "Игры"

    def save(self, *args, **kwargs):
        date_slug = slugify(translit_to_eng(str(self.date)))
        opponent_slug = slugify(translit_to_eng(self.opponent))
        fc_almaz_slug = "fc-almaz"

        if self.is_home:
            self.slug = f"{fc_almaz_slug}-{opponent_slug}-{date_slug}"
        else:
            self.slug = f"{opponent_slug}-{fc_almaz_slug}-{date_slug}"
        super().save(*args, **kwargs) 
