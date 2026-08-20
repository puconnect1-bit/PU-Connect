import os
import django

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pu_mp.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat_app.routing
import redis.exceptions


class RedisConnectionErrorMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            await self.app(scope, receive, send)
        except redis.exceptions.ConnectionError as e:
            if scope["type"] == "websocket":
                msg = "Redis connection error during WebSocket handling"
                print(msg + " - suppressed: " + str(e))
            else:
                raise


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": RedisConnectionErrorMiddleware(
        AuthMiddlewareStack(
            URLRouter(
                chat_app.routing.websocket_urlpatterns
            )
        )
    ),
})
