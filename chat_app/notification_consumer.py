import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .channel_utils import group_add_retry, group_discard_retry


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user_group_name = f'user_{user.id}'

        # Join personal group — retry a few times on transient Redis errors
        # before giving up, so a brief channel-layer blip doesn't reject the
        # handshake outright.
        try:
            await group_add_retry(self.channel_layer, self.user_group_name, self.channel_name)
        except Exception as e:
            print(f"Failed to join notification group for user {user.id}: {e}")
            await self.close()
            return

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            try:
                await group_discard_retry(self.channel_layer, self.user_group_name, self.channel_name)
            except Exception as e:
                print(f"Error leaving notification group on disconnect: {e}")

    # Receive notification from group
    async def notification_message(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps(event['data']))
