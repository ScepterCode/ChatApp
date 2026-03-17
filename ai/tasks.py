# ai/tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

try:
    from .sentiment import SentimentAnalyzer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    SentimentAnalyzer = None


@shared_task(bind=True, max_retries=3)
def analyze_sentiment_task(self, message_id: str, room_id: str, content: str):
    """
    Runs sentiment analysis on a message and broadcasts
    the result back to the room via WebSocket.
    
    Args:
        message_id: UUID of the message
        room_id:    UUID of the room (for channel group name)
        content:    message text to analyze
    
    Time complexity:  O(n) where n is content length
    Space complexity: O(1)
    """
    try:
        from chat.models import Message
        
        # run sentiment analysis
        result = SentimentAnalyzer.analyze(content)
        
        # update message in DB
        Message.objects.filter(id=message_id).update(
            sentiment=result['sentiment'],
            sentiment_score=result['sentiment_score'],
        )
        
        # broadcast sentiment update to room
        # so frontend updates the message indicator in realtime
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room_id}',
            {
                'type':            'sentiment_update',
                'message_id':      message_id,
                'sentiment':       result['sentiment'],
                'sentiment_score': result['sentiment_score'],
            }
        )
        
    except Exception as exc:
        # retry up to 3 times if something fails
        raise self.retry(exc=exc, countdown=5)