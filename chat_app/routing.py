from django.urls import re_path
from . import consumers, notification_consumer, presence_consumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<conv_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/$', notification_consumer.NotificationConsumer.as_asgi()),
    re_path(r'ws/presence/$', presence_consumer.PresenceConsumer.as_asgi()),
]
