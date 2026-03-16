#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from chat.models import Room, Membership, Message, JoinRequest

def cleanup_groups():
    print("🧹 Starting group cleanup...")
    
    # Count existing data
    room_count = Room.objects.count()
    membership_count = Membership.objects.count()
    message_count = Message.objects.count()
    request_count = JoinRequest.objects.count()
    
    print(f"📊 Current data:")
    print(f"   - Rooms: {room_count}")
    print(f"   - Memberships: {membership_count}")
    print(f"   - Messages: {message_count}")
    print(f"   - Join Requests: {request_count}")
    
    if room_count == 0:
        print("✅ No groups to clean up!")
        return
    
    # Delete all data
    print("\n🗑️  Deleting all group data...")
    
    # Delete in proper order to avoid foreign key constraints
    deleted_requests = JoinRequest.objects.all().delete()[0]
    deleted_messages = Message.objects.all().delete()[0]
    deleted_memberships = Membership.objects.all().delete()[0]
    deleted_rooms = Room.objects.all().delete()[0]
    
    print(f"✅ Cleanup complete!")
    print(f"   - Deleted {deleted_rooms} rooms")
    print(f"   - Deleted {deleted_memberships} memberships")
    print(f"   - Deleted {deleted_messages} messages")
    print(f"   - Deleted {deleted_requests} join requests")
    
    print("\n🎉 Database is now clean and ready for fresh groups!")

if __name__ == '__main__':
    cleanup_groups()