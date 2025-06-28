# Gunicorn configuration for Django
import multiprocessing

bind = '0.0.0.0:8000'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gthread'
threads = 2
max_requests = 1000
max_requests_jitter = 50
timeout = 60
keepalive = 5

# Security
secure_scheme_headers = { 'X-Forwarded-Proto': 'https' }
proxy_allow_ips = '*'

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
