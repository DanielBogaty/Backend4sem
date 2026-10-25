# FC Almaz - Запуск проекта

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