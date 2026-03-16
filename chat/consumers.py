# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from ai.toxicity import ToxicityAnalyzer
from ai.tasks import analyze_sentiment_task


class ChatConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_id    = self.scope['url_route']['kwargs']['room_id']
        self.room_group  = f'chat_{self.room_id}'
        self.user        = self.scope['user']
        
        # reject unauthenticated connections
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # verify user is a member of this room
        is_member = await self.check_membership()
        if not is_member:
            await self.close()
            return
        
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.mark_online(True)
        await self.accept()
    
    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)
        await self.mark_online(False)
    
    async def receive(self, text_data):
        data    = json.loads(text_data)
        msg_type = data.get('type', 'chat_message')
        
        if msg_type == 'chat_message':
            await self.handle_chat_message(data)
        elif msg_type == 'typing':
            await self.handle_typing(data)
        elif msg_type == 'read_receipt':
            await self.handle_read_receipt()
    
    async def handle_chat_message(self, data):
        content = data.get('content', '').strip()
        
        if not content:
            return
        
        # ── ENGINE 1: TOXICITY GATE ──────────────────────────
        toxicity = ToxicityAnalyzer.analyze(content)
        
        if toxicity['is_blocked']:
            # send rejection only back to sender, room never sees it
            await self.send(text_data=json.dumps({
                'type':    'error',
                'message': 'Message blocked: toxic content detected',
            }))
            return
        # ─────────────────────────────────────────────────────
        
        # save message to DB
        message = await self.save_message(
            content=content,
            toxicity_score=toxicity['toxicity_score'],
            is_flagged=toxicity['is_flagged'],
        )
        
        # build broadcast payload
        payload = {
            'type':            'chat_message',
            'id':              str(message.id),
            'content':         content,
            'sender': {
                'id':       str(self.user.id),
                'username': self.user.username,
            },
            'timestamp':       message.timestamp.isoformat(),
            'is_flagged':      toxicity['is_flagged'],
            'toxicity_score':  toxicity['toxicity_score'],
            'sentiment':       None,   # filled in by Engine 2 shortly after
            'sentiment_score': None,
        }
        
        # broadcast to everyone in room
        await self.channel_layer.group_send(
            self.room_group,
            {**payload, 'type': 'chat_message'}
        )
        
        # ── ENGINE 2: SENTIMENT TASK (background) ────────────
        analyze_sentiment_task.delay(
            message_id=str(message.id),
            room_id=self.room_id,
            content=content,
        )
        # ─────────────────────────────────────────────────────
    
    async def handle_typing(self, data):
        # broadcast typing indicator to room (not saved to DB)
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type':     'typing_indicator',
                'username': self.user.username,
                'is_typing': data.get('is_typing', False),
            }
        )
    
    async def handle_read_receipt(self):
        await self.update_last_read()
    
    # ── EVENT HANDLERS (called by channel layer) ──────────────
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def sentiment_update(self, event):
        # Engine 2 broadcasts this after analyzing sentiment
        # frontend uses it to update the mood indicator on the message
        await self.send(text_data=json.dumps(event))
    
    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps(event))
    
    # ── DATABASE HELPERS ──────────────────────────────────────
    
    @database_sync_to_async
    def check_membership(self):
        from chat.models import Membership
        return Membership.objects.filter(
            user=self.user,
            room_id=self.room_id
        ).exists()
    
    @database_sync_to_async
    def save_message(self, content, toxicity_score, is_flagged):
        from chat.models import Message
        return Message.objects.create(
            room_id=self.room_id,
            sender=self.user,
            content=content,
            toxicity_score=toxicity_score,
            is_flagged=is_flagged,
        )
    
    @database_sync_to_async
    def mark_online(self, status: bool):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        update = {'is_online': status}
        if not status:
            update['last_seen'] = timezone.now()
        User.objects.filter(id=self.user.id).update(**update)
    
    @database_sync_to_async
    def update_last_read(self):
        from chat.models import Membership
        Membership.objects.filter(
            user=self.user,
            room_id=self.room_id
        ).update(last_read_at=timezone.now())