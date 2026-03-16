from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from .models import Room, Membership, Message, DirectMessage, UserPresence, TypingIndicator
from .serializers import (
    RoomSerializer, MembershipSerializer, MessageSerializer, 
    DirectMessageSerializer, DirectMessageListSerializer,
    UserPresenceSerializer, TypingIndicatorSerializer
)

User = get_user_model()

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Room.objects.select_related('admin').prefetch_related('memberships')
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(id__icontains=search)
            )
        return queryset
    
    def perform_create(self, serializer):
        room = serializer.save(admin=self.request.user)
        Membership.objects.create(user=self.request.user, room=room)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        room = self.get_object()
        username = request.data.get('username')
        
        if not username:
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(username=username)
            membership, created = Membership.objects.get_or_create(user=user, room=room)
            
            if created:
                return Response({'message': f'{username} added to room'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': f'{username} is already a member'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        room = self.get_object()
        
        if room.admin == request.user:
            return Response({'error': 'Admin cannot leave room. Transfer ownership or delete room.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            membership = Membership.objects.get(user=request.user, room=room)
            membership.delete()
            return Response({'message': 'Left room successfully'}, status=status.HTTP_200_OK)
        except Membership.DoesNotExist:
            return Response({'error': 'You are not a member of this room'}, 
                          status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def delete_room(self, request, pk=None):
        room = self.get_object()
        room_name = room.name
        room.delete()
        return Response({'message': f'Room "{room_name}" deleted successfully'}, 
                       status=status.HTTP_200_OK)

class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Membership.objects.select_related('user', 'room')
        room_id = self.request.query_params.get('room')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        return queryset

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Message.objects.select_related('sender', 'room').prefetch_related('reactions')
        room_id = self.request.query_params.get('room')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        return queryset.order_by('timestamp')
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class DirectMessageViewSet(viewsets.ModelViewSet):
    serializer_class = DirectMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DirectMessage.objects.select_related('sender', 'recipient').prefetch_related('reactions')
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
    
    @action(detail=False, methods=['get'])
    def conversations(self, request):
        user = request.user
        conversations = []
        
        sent_to = DirectMessage.objects.filter(sender=user).values_list('recipient', flat=True).distinct()
        received_from = DirectMessage.objects.filter(recipient=user).values_list('sender', flat=True).distinct()
        
        all_contacts = set(list(sent_to) + list(received_from))
        
        for contact_id in all_contacts:
            latest_message = DirectMessage.objects.filter(
                Q(sender=user, recipient_id=contact_id) | 
                Q(sender_id=contact_id, recipient=user)
            ).select_related('sender', 'recipient').order_by('-timestamp').first()
            
            if latest_message:
                conversations.append(latest_message)
        
        conversations.sort(key=lambda x: x.timestamp, reverse=True)
        
        serializer = DirectMessageListSerializer(conversations, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def with_user(self, request):
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid user_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        messages = DirectMessage.objects.filter(
            Q(sender=request.user, recipient_id=user_id) |
            Q(sender_id=user_id, recipient=request.user)
        ).select_related('sender', 'recipient').order_by('timestamp')
        
        DirectMessage.objects.filter(
            sender_id=user_id, 
            recipient=request.user, 
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        serializer = DirectMessageSerializer(messages, many=True)
        return Response(serializer.data)

class UserPresenceViewSet(viewsets.ModelViewSet):
    serializer_class = UserPresenceSerializer
    permission_classes = [IsAuthenticated]
    queryset = UserPresence.objects.all()

class TypingIndicatorViewSet(viewsets.ModelViewSet):
    serializer_class = TypingIndicatorSerializer
    permission_classes = [IsAuthenticated]
    queryset = TypingIndicator.objects.all()



