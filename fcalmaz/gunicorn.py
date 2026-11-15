from os import environ


def resolve_workers():
    return int(environ.get('WEB_CONCURRENCY', '2'))


bind = '0.0.0.0:' + environ.get('PORT', '8000')
workers = resolve_workers()
worker_class = 'gevent'
worker_tmp_dir = '/tmp'

max_requests = 1000
max_requests_jitter = 50
timeout = 60
graceful_timeout = 30
keepalive = 5

env = {
    'DJANGO_SETTINGS_MODULE': 'fcalmaz.settings'
}

name = 'fcalmaz'