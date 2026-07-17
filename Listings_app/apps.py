from django.apps import AppConfig


class ListingsAppConfig(AppConfig):
    name = 'Listings_app'

    def ready(self):
        import Listings_app.signals

