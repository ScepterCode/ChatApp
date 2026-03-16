# chat/consumers_minimal.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

class MinimalChatConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group = f'chat_{self.room_id}'
        
        print(f"🔌 MINIMAL WebSocket connect attempt - Room: {self.room_id}")
        
        # Accept all connections without any checks
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()
        
        print(f"🎉 MINIMAL WebSocket connection accepted for room {self.room_id}")
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'system_message',
            'message': f'Connected to room {self.room_id} (minimal mode)',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def disconnect(self, code):
        print(f"🔌 MINIMAL WebSocket disconnected: {code}")
        await self.channel_layer.group_discard(self.room_group, self.channel_name)
    
    async def receive(self, text_data):
        print(f"📥 MINIMAL WebSocket received: {text_data}")
        data = json.loads(text_data)
        msg_type = data.get('type', 'chat_message')
        
        if msg_type == 'chat_message':
            content = data.get('content', '').strip()
            
            if not content:
                return
            
            # Build broadcast payload
            payload = {
                'type': 'chat_message',
                'id': 'test-id',
                'content': content,
                'sender': {
                    'id': 'test-user',
                    'username': 'TestUser',
                },
                'timestamp': timezone.now().isoformat(),
                'is_flagged': False,
                'toxicity_score': 0.0,
                'sentiment': 'NEUTRAL',
                'sentiment_score': 0.0,
            }
            
            # Broadcast to everyone in room
            await self.channel_layer.group_send(
                self.room_group,
                {**payload, 'type': 'chat_message'}
            )
    
    # Event handlers
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))