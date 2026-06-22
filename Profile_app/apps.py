from django.apps import AppConfig


class ProfileConfig(AppConfig):
    name = 'Profile_app'

    def ready(self):
        import Profile_app.signals
