import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Conversation, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.conv_id = int(self.scope['url_route']['kwargs']['conv_id'])
            self.room_group_name = f'chat_{self.conv_id}'
            
            user = self.scope.get('user')
            if not user or not user.is_authenticated:
                print(f"Connection rejected: Unauthenticated user")
                await self.close()
                return

            print(f"User {user.username} connecting to {self.room_group_name}")

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
        except Exception as e:
            print(f"Connection error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            user = self.scope.get('user')

            if not user or not user.is_authenticated:
                return

            msg_type = data.get('type', 'message')

            # ── Typing signal — broadcast, do not save ──
            if msg_type == 'typing':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_signal',
                        'sender_id': user.id,
                        'is_typing': bool(data.get('is_typing')),
                    }
                )
                return

            # ── Recording signal — broadcast, do not save ──
            if msg_type == 'recording':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'recording_signal',
                        'sender_id': user.id,
                        'is_recording': bool(data.get('is_recording')),
                    }
                )
                return

            # ── Read receipt ──
            if msg_type == 'read_receipt':
                message_ids = data.get('message_ids', [])
                if message_ids:
                    await self.mark_messages_read(message_ids, user.id)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'read_receipt',
                            'message_ids': message_ids,
                            'reader_id': user.id,
                        }
                    )
                return

            # ── Delete message ──
            if msg_type == 'delete':
                message_id = data.get('message_id')
                if message_id:
                    deleted = await self.delete_message(message_id, user.id)
                    if deleted:
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'message_deleted',
                                'message_id': message_id,
                            }
                        )
                return

            # ── Normal message ──
            reply_to_id = data.get('reply_to_id')
            saved_msg = await self.save_message(
                user.id,
                data.get('message'),
                data.get('image_url'),
                data.get('voice_url'),
                data.get('voice_duration', 0),
                data.get('meetup_spot'),
                data.get('meetup_time'),
                reply_to_id,
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'msg_id': saved_msg.id,
                    'message': data.get('message'),
                    'image_url': data.get('image_url'),
                    'voice_url': data.get('voice_url'),
                    'voice_duration': data.get('voice_duration'),
                    'meetup_spot': data.get('meetup_spot'),
                    'meetup_time': data.get('meetup_time'),
                    'reply_to_id': reply_to_id,
                    'sender_id': user.id,
                    'sender_username': user.username,
                    'timestamp': saved_msg.timestamp.strftime("%I:%M %p"),
                }
            )
        except Exception as e:
            print(f"Receive error: {e}")

    # Receive message from room group
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'msg_id': event.get('msg_id'),
            'message': event['message'],
            'image_url': event.get('image_url'),
            'voice_url': event.get('voice_url'),
            'voice_duration': event.get('voice_duration'),
            'meetup_spot': event.get('meetup_spot'),
            'meetup_time': event.get('meetup_time'),
            'reply_to_id': event.get('reply_to_id'),
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp'],
        }))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_ids': event['message_ids'],
            'reader_id': event['reader_id'],
        }))

    async def typing_signal(self, event):
        if event['sender_id'] == self.scope['user'].id:
            return  # don't echo back to the sender
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'sender_id': event['sender_id'],
            'is_typing': event['is_typing'],
        }))

    async def recording_signal(self, event):
        if event['sender_id'] == self.scope['user'].id:
            return  # don't echo back to the sender
        await self.send(text_data=json.dumps({
            'type': 'recording',
            'sender_id': event['sender_id'],
            'is_recording': event['is_recording'],
        }))

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id'],
        }))

    @database_sync_to_async
    def mark_messages_read(self, message_ids, reader_id):
        Message.objects.filter(
            id__in=message_ids,
            conversation_id=self.conv_id
        ).exclude(sender_id=reader_id).update(is_read=True)

    @database_sync_to_async
    def delete_message(self, message_id, user_id):
        try:
            msg = Message.objects.get(id=message_id, conversation_id=self.conv_id)
            # Only allow sender to delete their own messages
            if msg.sender_id == user_id:
                msg.is_deleted = True
                msg.deleted_at = timezone.now()
                msg.save(update_fields=['is_deleted', 'deleted_at'])
                return True
            return False
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, sender_id, text, image_url, voice_url, voice_duration, meetup_spot, meetup_time, reply_to_id=None):
        user = User.objects.get(id=sender_id)
        conv = Conversation.objects.get(id=self.conv_id)
        conv.save()
        reply_to_msg = Message.objects.filter(id=reply_to_id).first() if reply_to_id else None
        msg = Message.objects.create(
            conversation=conv,
            sender=user,
            text=text,
            image_url=image_url,
            voice_url=voice_url,
            voice_duration=voice_duration or 0,
            meetup_spot=meetup_spot,
            meetup_time=meetup_time,
            reply_to=reply_to_msg,
        )
        return msg