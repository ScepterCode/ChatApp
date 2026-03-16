from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Room(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_rooms')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='room_memberships')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'room')
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} in {self.room.name}"

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    
    # AI engine fields
    sentiment = models.CharField(max_length=10, null=True, blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    toxicity_score = models.FloatField(null=True, blank=True)
    is_flagged = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['room', 'timestamp']),
            models.Index(fields=['sender', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"

class DirectMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_direct_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_direct_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['sender', 'recipient', 'timestamp']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.content[:50]}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

class UserPresence(models.Model):
    ONLINE = 'online'
    AWAY = 'away'
    OFFLINE = 'offline'
    
    STATUS_CHOICES = [
        (ONLINE, 'Online'),
        (AWAY, 'Away'),
        (OFFLINE, 'Offline'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='presence')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=OFFLINE)
    last_seen = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=False, db_index=True)  # Add index for performance
    
    class Meta:
        verbose_name_plural = 'User Presences'
        indexes = [
            models.Index(fields=['is_online', 'status']),  # Composite index for online queries
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.status}"
    
    def set_online(self):
        self.status = self.ONLINE
        self.is_online = True
        self.last_seen = timezone.now()
        self.save()
    
    def set_away(self):
        self.status = self.AWAY
        self.is_online = False
        self.save()
    
    def set_offline(self):
        self.status = self.OFFLINE
        self.is_online = False
        self.last_seen = timezone.now()
        self.save()

class TypingIndicator(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='typing_indicators')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='typing_users', null=True, blank=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='typing_from', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True, db_index=True)  # Add index for cleanup queries
    
    class Meta:
        indexes = [
            models.Index(fields=['room', 'timestamp']),
            models.Index(fields=['recipient', 'timestamp']),
            models.Index(fields=['timestamp']),  # For cleanup operations
        ]
    
    def __str__(self):
        if self.room:
            return f"{self.user.username} typing in {self.room.name}"
        return f"{self.user.username} typing to {self.recipient.username}"

class MessageReaction(models.Model):
    EMOJI_CHOICES = [
        ('👍', 'Thumbs Up'),
        ('❤️', 'Heart'),
        ('😂', 'Laughing'),
        ('😮', 'Surprised'),
        ('😢', 'Sad'),
        ('🔥', 'Fire'),
        ('🎉', 'Party'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions', null=True, blank=True)
    direct_message = models.ForeignKey(DirectMessage, on_delete=models.CASCADE, related_name='reactions', null=True, blank=True)
    emoji = models.CharField(max_length=10, choices=EMOJI_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ('user', 'message', 'emoji'),
            ('user', 'direct_message', 'emoji'),
        ]
    
    def __str__(self):
        msg_type = "message" if self.message else "DM"
        return f"{self.user.username} reacted {self.emoji} to {msg_type}"
