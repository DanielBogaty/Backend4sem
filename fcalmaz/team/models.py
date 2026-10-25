from django.db import models
from django.urls import reverse
from django.template.defaultfilters import slugify


def translit_to_eng(s: str) -> str:
    d = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
         'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'к': 'k',
         'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
         'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch',
         'ш': 'sh', 'щ': 'shch', 'ь': '', 'ы': 'y', 'ъ': '', 'э': 'r', 'ю': 'yu', 'я': 'ya'}

    return "".join(map(lambda x: d[x] if d.get(x, False) else x, s.lower()))



class Player(models.Model):
    name = models.CharField(max_length=255, verbose_name="Имя")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="Slug")
    photo = models.ImageField(upload_to="player_photo/%y/%m/%d", default=None, blank=True, null=True, verbose_name="Фото")
    pos = models.ForeignKey('Position', on_delete=models.PROTECT, verbose_name="Позиция")
    height = models.PositiveIntegerField(blank=True, null=True, verbose_name="Рост (см)")
    weight = models.PositiveIntegerField(blank=True, null=True, verbose_name="Вес (кг)")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Дата рождения")
    nationality = models.CharField(max_length=255, blank=True, verbose_name="Национальность")

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('team:player', kwargs={'slug_player': self.slug})
    
    class Meta:
        verbose_name = "Футболист"
        verbose_name_plural = "Состав команды"

    def save(self, *args, **kwargs):
        self.slug = slugify(translit_to_eng(self.name))
        super().save(*args, **kwargs)

    def get_height_display(self):
        return f"{self.height} см" if self.height else "N/a"

    def get_weight_display(self):
        return f"{self.weight} кг" if self.weight else "N/a"

    def get_birth_date_display(self):
        return self.birth_date.strftime("%d.%m.%Y") if self.birth_date else "N/a"

    def get_nationality_display(self):
        return self.nationality if self.nationality else "N/a"


class Position(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Позиция"
        verbose_name_plural = "Позиции"