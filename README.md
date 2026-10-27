# ⚽ FC Almaz - Backend API

REST API для интернет-магазина футбольного клуба, разработанное на Django REST Framework.  
Реализует аутентификацию, каталог товаров с фильтрацией и кэшированием, управление корзиной и промокодами.

## 🛠 Технологический стек

- **Backend:** Python 3.12, Django 5.2, Django REST Framework
- **База данных:** PostgreSQL 17 (Локально через Docker / Облачно через **Neon.tech**)
- **ORM:** Django ORM (все запросы фильтрации/сортировки выполняются на уровне СУБД)
- **Кэширование:** Redis (TTL 120 сек для каталога, автоматическая инвалидация при изменениях)
- **Медиафайлы:** Cloudinary (облачное хранилище для изображений товаров и пользователей)
- **Безопасность:** JWT (SimpleJWT) + Хеширование паролей **Argon2**
- **Документация:** OpenAPI / Swagger (drf-spectacular)
- **Контейнеризация:** Docker, Docker Compose (Multi-stage build)

---

## 📋 Предварительные требования

Для запуска проекта на твоем компьютере должны быть установлены:
1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) (включая Docker Compose)
2. [Git](https://git-scm.com/)
3. Python 3.12+ (опционально, для виртуального окружения IDE)

---

## 🚀 Первый запуск проекта

Выполни следующие шаги в терминале (PowerShell / Bash) из корневой папки проекта:

1. Клонирование и подготовка окружения
```powershell
# Создай и активируй виртуальное окружение (для корректной работы IDE)
python -m venv djvenv
.\djvenv\Scripts\Activate.ps1

# Установи зависимости (для подсветки синтаксиса и линтеров в IDE)
pip install -r fcalmaz/requirements.txt

# Создай служебные папки
New-Item -ItemType Directory -Force -Path .\logs
New-Item -ItemType Directory -Force -Path .\media

2. Настройка переменных окружения
Создай файл .env в корневой папке проекта на основе .env.example и заполни его реальными данными (ключи Cloudinary, строка подключения Neon.tech и т.д.).
⚠️ Важно: Никогда не коммить файл .env в репозиторий!

3. Запуск контейнеров и инициализация
# 1. Сборка и запуск всех сервисов (Django, PostgreSQL, Redis, Nginx, Adminer)
docker compose up -d --build
# 2. Применение миграций к базе данных
docker compose exec fcalmaz python manage.py migrate
# 3. Создание суперпользователя (администратора)
docker compose exec fcalmaz python manage.py createsuperuser
# 4. Сборка статических файлов для Nginx и WhiteNoise
docker compose exec fcalmaz python manage.py collectstatic --noinput
# (Опционально) Загрузи начальные данные, если есть db.json
docker compose exec fcalmaz python manage.py loaddata db.json

Повседневное использование
# Запуск проекта
# Если контейнеры были остановлены, просто запусти их:
docker compose up -d
# Остановка проекта
# Останавливает контейнеры, сохраняя все данные в базе данных и Redis:
docker compose down
# Полный сброс проекта ⚠️
# Внимание: Эта команда удалит все локальные данные базы данных и кэш Redis! Используйте только для полной переустановки.
docker compose down -v

Доступ к сервисам
# После запуска сервисы доступны по следующим адресам:
# Основной сайт: http://localhost
# Админ-панель: http://localhost/admin/
# API документация (Swagger): http://localhost:8000/api/schema/swagger/
# Adminer (управление БД): http://localhost:8080

API Endpoints
# Аутентификация
POST /api/auth/register — Регистрация нового пользователя
POST /api/auth/login — Логин и получение JWT токенов (Access / Refresh)
# Каталог товаров
GET /api/products — Список товаров (поддерживает search, min_price, max_price, min_rating, ordering, page, limit)
GET /api/products/:id — Детальная информация о товаре
POST /api/products — Создание товара (только роль admin)
DELETE /api/products/:id — Удаление товара (только роль admin, вызывает сброс кэша)
# Корзина и промокоды
GET /api/cart — Получить содержимое корзины текущего пользователя
POST /api/cart/items — Добавить товар в корзину
PATCH /api/cart/items/:id — Изменить количество товара в корзине
DELETE /api/cart/items/:id — Удалить позицию из корзины
POST /api/cart/apply-promo — Применить промокод и рассчитать итоговую стоимость