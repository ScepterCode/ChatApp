# chat/consumers.py
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

# Optional AI imports - graceful fallback if not available
try:
    from ai.toxicity import ToxicityAnalyzer
    from ai.sentiment import SentimentAnalyzer
    AI_AVAILABLE = True
except ImportError:
    # AI modules not available - create fallback classes
    AI_AVAILABLE = False
    
    class ToxicityAnalyzer:
        @classmethod
        def analyze(cls, text: str) -> dict:
            # Simple keyword-based fallback
            toxic_keywords = ['spam', 'hate', 'abuse', 'toxic']
            has_toxic = any(word in text.lower() for word in toxic_keywords)
            return {
                'toxicity_score': 0.9 if has_toxic else 0.1,
                'is_blocked': has_toxic,
                'is_flagged': False,
            }
    
    class SentimentAnalyzer:
        @classmethod
        def analyze(cls, text: str) -> dict:
            # Simple keyword-based fallback
            positive_words = ['good', 'great', 'love', 'awesome']
            negative_words = ['bad', 'hate', 'terrible', 'awful']
            text_lower = text.lower()
            
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            if pos_count > neg_count:
                return {'sentiment': 'positive', 'sentiment_score': 0.7}
            elif neg_count > pos_count:
                return {'sentiment': 'negative', 'sentiment_score': 0.7}
            else:
                return {'sentiment': 'neutral', 'sentiment_score': 0.6}

# Create a thread pool at module level for background tasks
_executor = ThreadPoolExecutor(max_workers=4)


class ChatConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group = f'chat_{self.room_id}'
        self.user = self.scope['user']
        
        print(f"🔌 WebSocket connect attempt - Room: {self.room_id}, User: {self.user}")
        
        # For testing: Accept all connections
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()
        
        print(f"🎉 WebSocket connection accepted for room {self.room_id}")
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'system_message',
            'message': f'Connected to room {self.room_id}',
            'timestamp': timezone.now().isoformat()
        }))
    
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
            # Send rejection only back to sender, room never sees it
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message blocked: toxic content detected',
            }))
            return
        # ─────────────────────────────────────────────────────
        
        # Save message to database
        message = await self.save_message(
            content=content,
            toxicity_score=toxicity['toxicity_score'],
            is_flagged=toxicity['is_flagged'],
        )
        
        # Build broadcast payload
        payload = {
            'type': 'chat_message',
            'id': str(message.id),
            'content': content,
            'sender': {
                'id': str(self.user.id),
                'username': self.user.username,
            },
            'timestamp': message.timestamp.isoformat(),
            'is_flagged': toxicity['is_flagged'],
            'toxicity_score': toxicity['toxicity_score'],
            'sentiment': None,   # Filled in by Engine 2 shortly after
            'sentiment_score': None,
        }
        
        # Broadcast to everyone in room
        await self.channel_layer.group_send(
            self.room_group,
            {**payload, 'type': 'chat_message'}
        )
        
        # ── ENGINE 2: SENTIMENT TASK (background asyncio) ────────────
        # Run sentiment analysis in background thread - no Celery needed
        asyncio.ensure_future(
            self.run_sentiment_async(str(message.id), content)
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
    
    async def run_sentiment_async(self, message_id: str, content: str):
        """
        Runs sentiment analysis in a thread pool
        so it doesn't block the WebSocket event loop.
        
        Time complexity:  O(n)
        Space complexity: O(1)
        """
        loop = asyncio.get_event_loop()
        
        # Run the blocking ML model in a thread
        result = await loop.run_in_executor(
            _executor,
            SentimentAnalyzer.analyze,
            content
        )
        
        # Update database
        await self.update_sentiment_in_db(message_id, result)
        
        # Broadcast sentiment update to room
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type': 'sentiment_update',
                'message_id': message_id,
                'sentiment': result['sentiment'],
                'sentiment_score': result['sentiment_score'],
            }
        )
    
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
        
        # Check if the user model has online status fields
        if hasattr(User, 'is_online'):
            update = {'is_online': status}
            if not status and hasattr(User, 'last_seen'):
                update['last_seen'] = timezone.now()
            User.objects.filter(id=self.user.id).update(**update)
        # If no online status fields, just skip this functionality
    
    @database_sync_to_async
    def update_last_read(self):
        from chat.models import Membership
        Membership.objects.filter(
            user=self.user,
            room_id=self.room_id
        ).update(last_read_at=timezone.now())
    
    @database_sync_to_async
    def update_sentiment_in_db(self, message_id: str, result: dict):
        """Update message with sentiment analysis results."""
        from chat.models import Message
        Message.objects.filter(id=message_id).update(
            sentiment=result['sentiment'],
            sentiment_score=result['sentiment_score'],
        )