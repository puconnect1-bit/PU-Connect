import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        
        self.user_group_name = f'user_{user.id}'
        
        # Join personal group — handle Redis connection failures gracefully
        try:
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
        except Exception as e:
            print(f"Failed to join notification group for user {user.id}: {e}")
            await self.close()
            return
            
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            try:
                await self.channel_layer.group_discard(
                    self.user_group_name,
                    self.channel_name
                )
            except Exception as e:
                print(f"Error leaving notification group on disconnect: {e}")

    # Receive notification from group
    async def notification_message(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps(event['data']))
