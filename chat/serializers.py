from rest_framework import serializers
from .models import (
    Room, Membership, Message, DirectMessage, 
    UserPresence, TypingIndicator, MessageReaction
)
from accounts.serializers import ProfileSerializer

class RoomSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Room
        fields = ('id', 'name', 'admin', 'admin_username', 'created_at', 'member_count')
        read_only_fields = ('admin', 'created_at')
    
    def get_member_count(self, obj):
        return obj.memberships.count()

class MembershipSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    
    class Meta:
        model = Membership
        fields = ('id', 'user', 'user_username', 'room', 'room_name', 'joined_at')
        read_only_fields = ('user', 'joined_at')

class MessageReactionSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ('id', 'user', 'user_username', 'emoji', 'timestamp')
        read_only_fields = ('user', 'timestamp')

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    reaction_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ('id', 'room', 'sender', 'sender_username', 'sender_id', 'content', 'timestamp', 
                 'edited_at', 'is_edited', 'reactions', 'reaction_count', 'sentiment', 'sentiment_score', 
                 'toxicity_score', 'is_flagged')
        read_only_fields = ('sender', 'timestamp', 'edited_at', 'is_edited', 'sentiment', 
                           'sentiment_score', 'toxicity_score', 'is_flagged')
    
    def get_reaction_count(self, obj):
        return obj.reactions.count()

class DirectMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    recipient_username = serializers.CharField(source='recipient.username', read_only=True)
    recipient_id = serializers.IntegerField(source='recipient.id', read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    reaction_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DirectMessage
        fields = ('id', 'sender', 'sender_username', 'sender_id', 'recipient', 'recipient_username', 
                  'recipient_id', 'content', 'timestamp', 'edited_at', 'is_edited', 'is_read', 'read_at', 'reactions', 'reaction_count')
        read_only_fields = ('sender', 'timestamp', 'edited_at', 'is_edited', 'is_read', 'read_at')
    
    def get_reaction_count(self, obj):
        return obj.reactions.count()

class DirectMessageListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing conversations"""
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DirectMessage
        fields = ('other_user', 'last_message', 'unread_count')
    
    def get_other_user(self, obj):
        request_user = self.context['request'].user
        other = obj.sender if obj.recipient == request_user else obj.recipient
        return ProfileSerializer(other).data
    
    def get_last_message(self, obj):
        return obj.content[:100]
    
    def get_unread_count(self, obj):
        request_user = self.context['request'].user
        if obj.recipient == request_user and not obj.is_read:
            return 1
        return 0

class UserPresenceSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    
    class Meta:
        model = UserPresence
        fields = ('id', 'user', 'user_id', 'user_username', 'status', 'is_online', 'last_seen')
        read_only_fields = ('last_seen',)

class TypingIndicatorSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True, allow_null=True)
    recipient_username = serializers.CharField(source='recipient.username', read_only=True, allow_null=True)
    
    class Meta:
        model = TypingIndicator
        fields = ('id', 'user', 'user_username', 'room', 'room_name', 'recipient', 'recipient_username', 'timestamp')
        read_only_fields = ('timestamp',)
