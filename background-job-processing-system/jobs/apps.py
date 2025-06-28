from django.apps import AppConfig


class JobsConfig(AppConfig):
    """AppConfig for the jobs app, ensures tasks are imported for Celery."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'

    def ready(self):
        # Import tasks to ensure Celery discovers them
        import jobs.tasks
