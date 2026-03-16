from django.contrib import admin
from .models import (
    Room, Membership, Message, DirectMessage,
    UserPresence, TypingIndicator, MessageReaction
)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin', 'created_at', 'member_count')
    list_filter = ('created_at',)
    search_fields = ('name', 'admin__username')
    readonly_fields = ('created_at',)
    
    def member_count(self, obj):
        return obj.memberships.count()
    member_count.short_description = 'Members'

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'joined_at')
    list_filter = ('joined_at', 'room')
    search_fields = ('user__username', 'room__name')
    readonly_fields = ('joined_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'timestamp', 'preview', 'is_edited')
    list_filter = ('timestamp', 'room', 'is_edited')
    search_fields = ('sender__username', 'room__name', 'content')
    readonly_fields = ('timestamp', 'edited_at')

    def preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    preview.short_description = 'Message Preview'

@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'timestamp', 'preview', 'is_read', 'is_edited')
    list_filter = ('timestamp', 'is_read', 'is_edited')
    search_fields = ('sender__username', 'recipient__username', 'content')
    readonly_fields = ('timestamp', 'edited_at', 'read_at')
    
    def preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    preview.short_description = 'Message Preview'

@admin.register(UserPresence)
class UserPresenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'is_online', 'last_seen')
    list_filter = ('status', 'is_online', 'last_seen')
    search_fields = ('user__username',)
    readonly_fields = ('last_seen',)

@admin.register(TypingIndicator)
class TypingIndicatorAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'recipient', 'timestamp')
    list_filter = ('timestamp', 'room')
    search_fields = ('user__username', 'room__name', 'recipient__username')
    readonly_fields = ('timestamp',)

@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'emoji', 'message', 'direct_message', 'timestamp')
    list_filter = ('emoji', 'timestamp')
    search_fields = ('user__username',)
    readonly_fields = ('timestamp',)
