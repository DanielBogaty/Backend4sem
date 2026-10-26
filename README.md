# FC Almaz - Запуск проекта
Воссоздай локальное виртуальное окружение (для IDE)
python -m venv djvenv
.\djvenv\Scripts\Activate.ps1
cd fcalmaz
pip install -r requirements.txt

Создай пустые служебные папки
New-Item -ItemType Directory -Force -Path .\logs
New-Item -ItemType Directory -Force -Path .\media

1. Запуск контейнеров   
docker compose up -d --build

2. Применение миграций базы данных
docker compose exec fcalmaz python manage.py migrate

3. Загрузка начальных данных (если есть файл db.json)
docker compose exec fcalmaz python manage.py loaddata db.json

4. Создание суперпользователя (администратора)
docker compose exec fcalmaz python manage.py createsuperuser

5. Сборка статических файлов для Nginx
docker compose exec fcalmaz python manage.py collectstatic --noinput

Доступ к сервисам
Основной сайт: http://localhost
Админ-панель: http://localhost/admin/
Adminer (управление БД): http://localhost:8080
(Сервер: postgres, Пользователь: fcalmaz, Пароль: 1234, База: fcalmaz_db)

Остановка проекта (сохраняя данные БД):
docker compose down

Полный сброс проекта (с удалением томов базы данных и Redis):
docker compose down -v


API Endpoints
Аутентификация
POST /api/auth/register — Регистрация пользователя
POST /api/auth/login — Логин и получение JWT токена

Товары
GET /api/products — Каталог товаров (поиск, фильтрация, сортировка, пагинация)
GET /api/products/:id — Детальная информация о товаре
POST /api/products — Создание товара (только admin)
DELETE /api/products/:id — Удаление товара (только admin)

Корзина
GET /api/cart — Получить корзину пользователя
POST /api/cart/items — Добавить товар в корзину
PATCH /api/cart/items/:id — Изменить количество товара
DELETE /api/cart/items/:id — Удалить товар из корзины
POST /api/cart/apply-promo — Применить промокод

Администрирование
/admin/ — Django Admin панель