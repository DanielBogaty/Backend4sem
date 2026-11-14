FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY fcalmaz/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

RUN groupadd -r groupdjango && useradd -r -g groupdjango userdj

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/www/fcalmaz

COPY --from=builder /install /usr/local
COPY fcalmaz/ .

ENV DJANGO_SECRET_KEY="build-key" DJANGO_ALLOWED_HOSTS="127.0.0.1 localhost"

RUN python manage.py collectstatic --noinput

RUN chown -R userdj:groupdjango /app/www/fcalmaz

USER userdj

EXPOSE 8000

CMD ["gunicorn", "-c", "gunicorn.py", "fcalmaz.wsgi:application"]