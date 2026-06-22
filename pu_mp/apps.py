from django.apps import AppConfig


class PuMpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pu_mp'

    def ready(self):
        from pu_mp.r2_db_sync import start_flush_thread
        start_flush_thread(interval=30)
