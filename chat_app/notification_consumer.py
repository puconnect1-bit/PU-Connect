import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
            
        self.user_group_name = f'user_{user.id}'
        
        # Join personal group
        print(f"DEBUG: NotificationConsumer connected for user {user.username}, group {self.user_group_name}")
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        print(f"DEBUG: NotificationConsumer disconnected for group {getattr(self, 'user_group_name', 'unknown')}")
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    # Receive notification from group
    async def notification_message(self, event):
        print(f"DEBUG: NotificationConsumer received group message: {event['data'].get('title')}")
        # Send notification to WebSocket
        await self.send(text_data=json.dumps(event['data']))
