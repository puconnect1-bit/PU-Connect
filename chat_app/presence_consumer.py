import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User


class PresenceConsumer(AsyncWebsocketConsumer):
    """
    One persistent WS connection per browser tab.
    connect  → mark user online, notify their conversation partners
    disconnect → mark user offline, notify their conversation partners
    """

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user_id = user.id
        self.user_group = f'presence_user_{user.id}'

        # Join own presence group (so others can push to us)
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()

        # Tell conversation partners we're online
        await self._broadcast_status('online')

    async def disconnect(self, close_code):
        if not hasattr(self, 'user_id'):
            return
        await self._broadcast_status('offline')
        await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def receive(self, text_data):
        # Client can send a ping to keep the connection alive; we ignore payload
        pass

    # ── Handler: receive a presence event pushed by another user ──
    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'presence',
            'user_id': event['user_id'],
            'status': event['status'],
        }))

    # ── Broadcast our status to all conversation partners ──
    async def _broadcast_status(self, status):
        partner_ids = await self._get_partner_ids()
        for pid in partner_ids:
            await self.channel_layer.group_send(
                f'presence_user_{pid}',
                {
                    'type': 'presence_update',
                    'user_id': self.user_id,
                    'status': status,
                }
            )

    @database_sync_to_async
    def _get_partner_ids(self):
        from .models import Conversation
        convs = Conversation.objects.filter(participants__id=self.user_id)
        ids = set()
        for c in convs:
            for pid in c.participants.exclude(id=self.user_id).values_list('id', flat=True):
                ids.add(pid)
        return list(ids)
