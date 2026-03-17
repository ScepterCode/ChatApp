# Polling-based chat views (no WebSockets needed)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import json

from .models import Room, Membership, Message, DirectMessage, UserPresence, TypingIndicator
from .serializers import MessageSerializer, RoomSerializer

User = get_user_model()

class PollingChatViewSet(viewsets.ViewSet):
    """Polling-based chat API - no WebSockets required"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """Send a message to a room"""
        room_id = request.data.get('room_id')
        content = request.data.get('content', '').strip()
        
        if not room_id or not content:
            return Response({'error': 'room_id and content are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if user is member of the room
            membership = Membership.objects.get(user=request.user, room_id=room_id)
            room = membership.room
            
            # Create message
            message = Message.objects.create(
                room=room,
                sender=request.user,
                content=content,
                toxicity_score=0.1,  # Default safe score
                sentiment='neutral',
                sentiment_score=0.6
            )
            
            # Update user's last activity
            UserPresence.objects.update_or_create(
                user=request.user,
                defaults={
                    'is_online': True,
                    'last_seen': timezone.now()
                }
            )
            
            # Update membership last read
            membership.last_read_at = timezone.now()
            membership.save()
            
            # Format message data for frontend compatibility
            message_data = {
                'id': str(message.id),
                'content': message.content,
                'sender': {
                    'id': str(message.sender.id),
                    'username': message.sender.username
                },
                'timestamp': message.timestamp.isoformat(),
                'sentiment': message.sentiment,
                'is_flagged': message.is_flagged
            }
            
            return Response({
                'success': True,
                'message': message_data
            })
            
        except Membership.DoesNotExist:
            return Response({'error': 'Not a member of this room'}, 
                          status=status.HTTP_403_FORBIDDEN)
        except Room.DoesNotExist:
            return Response({'error': 'Room not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def get_messages(self, request):
        """Get messages for a room (polling endpoint)"""
        room_id = request.query_params.get('room_id')
        since = request.query_params.get('since')  # Timestamp for incremental updates
        limit = int(request.query_params.get('limit', 50))
        
        if not room_id:
            return Response({'error': 'room_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if user is member of the room
            membership = Membership.objects.get(user=request.user, room_id=room_id)
            
            # Get messages
            messages = Message.objects.filter(room_id=room_id).select_related('sender')
            
            # If 'since' timestamp provided, only get newer messages
            if since:
                try:
                    since_dt = timezone.datetime.fromisoformat(since.replace('Z', '+00:00'))
                    messages = messages.filter(timestamp__gt=since_dt)
                except ValueError:
                    pass  # Invalid timestamp, ignore
            
            messages = messages.order_by('-timestamp')[:limit]
            messages = list(reversed(messages))  # Oldest first
            
            # Format messages for frontend compatibility
            message_data = [
                {
                    'id': str(m.id),
                    'content': m.content,
                    'sender': {
                        'id': str(m.sender.id),
                        'username': m.sender.username
                    },
                    'timestamp': m.timestamp.isoformat(),
                    'sentiment': m.sentiment,
                    'is_flagged': m.is_flagged
                }
                for m in messages
            ]
            
            return Response({
                'success': True,
                'messages': message_data,
                'room_id': room_id,
                'timestamp': timezone.now().isoformat(),
                'has_more': len(messages) == limit
            })
            
        except Membership.DoesNotExist:
            return Response({'error': 'Not a member of this room'}, 
                          status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=False, methods=['post'])
    def mark_typing(self, request):
        """Mark user as typing in a room"""
        room_id = request.data.get('room_id')
        is_typing = request.data.get('is_typing', True)
        
        if not room_id:
            return Response({'error': 'room_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if user is member of the room
            Membership.objects.get(user=request.user, room_id=room_id)
            
            if is_typing:
                # Create or update typing indicator
                TypingIndicator.objects.update_or_create(
                    user=request.user,
                    room_id=room_id,
                    defaults={'timestamp': timezone.now()}
                )
            else:
                # Remove typing indicator
                TypingIndicator.objects.filter(
                    user=request.user,
                    room_id=room_id
                ).delete()
            
            return Response({'success': True})
            
        except Membership.DoesNotExist:
            return Response({'error': 'Not a member of this room'}, 
                          status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=False, methods=['get'])
    def get_typing(self, request):
        """Get who's typing in a room"""
        room_id = request.query_params.get('room_id')
        
        if not room_id:
            return Response({'error': 'room_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if user is member of the room
            Membership.objects.get(user=request.user, room_id=room_id)
            
            # Get recent typing indicators (last 10 seconds)
            cutoff = timezone.now() - timedelta(seconds=10)
            typing_users = TypingIndicator.objects.filter(
                room_id=room_id,
                timestamp__gte=cutoff
            ).exclude(user=request.user).select_related('user')
            
            typing_list = [
                {
                    'user_id': t.user.id,
                    'username': t.user.username,
                    'timestamp': t.timestamp.isoformat()
                }
                for t in typing_users
            ]
            
            return Response({
                'success': True,
                'typing': typing_list,
                'room_id': room_id
            })
            
        except Membership.DoesNotExist:
            return Response({'error': 'Not a member of this room'}, 
                          status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=False, methods=['get'])
    def get_online_users(self, request):
        """Get online users in a room"""
        room_id = request.query_params.get('room_id')
        
        if not room_id:
            return Response({'error': 'room_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if user is member of the room
            Membership.objects.get(user=request.user, room_id=room_id)
            
            # Get room members who were online recently (last 5 minutes)
            cutoff = timezone.now() - timedelta(minutes=5)
            online_members = Membership.objects.filter(
                room_id=room_id
            ).select_related('user')
            
            online_list = []
            for membership in online_members:
                try:
                    # Check if user has recent presence
                    presence = UserPresence.objects.filter(user=membership.user).first()
                    if presence and presence.last_seen >= cutoff:
                        online_list.append({
                            'user_id': membership.user.id,
                            'username': membership.user.username,
                            'is_online': presence.is_online,
                            'last_seen': presence.last_seen.isoformat()
                        })
                    else:
                        # Include all members but mark as offline if no recent presence
                        online_list.append({
                            'user_id': membership.user.id,
                            'username': membership.user.username,
                            'is_online': False,
                            'last_seen': None
                        })
                except Exception as e:
                    # If there's any error, still include the user as offline
                    online_list.append({
                        'user_id': membership.user.id,
                        'username': membership.user.username,
                        'is_online': False,
                        'last_seen': None
                    })
            
            return Response({
                'success': True,
                'online_users': online_list,
                'room_id': room_id
            })
            
        except Membership.DoesNotExist:
            return Response({'error': 'Not a member of this room'}, 
                          status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=False, methods=['post'])
    def update_presence(self, request):
        """Update user's online presence"""
        UserPresence.objects.update_or_create(
            user=request.user,
            defaults={
                'is_online': True,
                'last_seen': timezone.now()
            }
        )
        
        return Response({'success': True})

# Simple function-based views for even simpler polling
@csrf_exempt
def poll_messages(request):
    """Simple polling endpoint for messages"""
    if request.method != 'GET':
        return JsonResponse({'error': 'GET only'}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    room_id = request.GET.get('room_id')
    since = request.GET.get('since')
    
    if not room_id:
        return JsonResponse({'error': 'room_id required'}, status=400)
    
    try:
        # Check membership
        Membership.objects.get(user=request.user, room_id=room_id)
        
        # Get messages
        messages = Message.objects.filter(room_id=room_id).select_related('sender')
        
        if since:
            try:
                since_dt = timezone.datetime.fromisoformat(since.replace('Z', '+00:00'))
                messages = messages.filter(timestamp__gt=since_dt)
            except ValueError:
                pass
        
        messages = messages.order_by('-timestamp')[:20]
        messages = list(reversed(messages))
        
        message_data = [
            {
                'id': str(m.id),
                'content': m.content,
                'sender': {
                    'id': str(m.sender.id),
                    'username': m.sender.username
                },
                'timestamp': m.timestamp.isoformat(),
                'sentiment': m.sentiment,
                'is_flagged': m.is_flagged
            }
            for m in messages
        ]
        
        return JsonResponse({
            'success': True,
            'messages': message_data,
            'timestamp': timezone.now().isoformat()
        })
        
    except Membership.DoesNotExist:
        return JsonResponse({'error': 'Not a member'}, status=403)