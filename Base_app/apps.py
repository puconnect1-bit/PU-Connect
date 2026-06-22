from django.apps import AppConfig


class BaseAppConfig(AppConfig):
    name = 'Base_app'

    def ready(self):
        import Base_app.signals
