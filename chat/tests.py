"""
Test suite for chat endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Room, Membership, Message, DirectMessage, UserPresence

User = get_user_model()


class RoomTestCase(TestCase):
    """Test room endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        self.client.force_authenticate(user=self.user1)
    
    def test_create_room(self):
        """Test room creation."""
        response = self.client.post(
            '/api/chat/rooms/',
            {'name': 'General'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'General')
        self.assertEqual(response.data['admin'], self.user1.id)
    
    def test_list_rooms(self):
        """Test list rooms."""
        room = Room.objects.create(name='General', admin=self.user1)
        Membership.objects.create(user=self.user1, room=room)
        
        response = self.client.get('/api/chat/rooms/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_join_room(self):
        """Test joining a room."""
        room = Room.objects.create(name='General', admin=self.user1)
        self.client.force_authenticate(user=self.user2)
        
        response = self.client.post(
            '/api/chat/memberships/',
            {'room': room.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Membership.objects.filter(user=self.user2, room=room).exists()
        )
    
    def test_leave_room(self):
        """Test leaving a room."""
        room = Room.objects.create(name='General', admin=self.user1)
        Membership.objects.create(user=self.user1, room=room)
        
        response = self.client.post(f'/api/chat/rooms/{room.id}/leave/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            Membership.objects.filter(user=self.user1, room=room).exists()
        )
    
    def test_add_member_as_admin(self):
        """Test adding member as room admin."""
        room = Room.objects.create(name='General', admin=self.user1)
        
        response = self.client.post(
            f'/api/chat/rooms/{room.id}/add_member/',
            {'username': 'user2'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Membership.objects.filter(user=self.user2, room=room).exists()
        )
    
    def test_add_member_not_admin(self):
        """Test adding member as non-admin."""
        room = Room.objects.create(name='General', admin=self.user2)
        
        response = self.client.post(
            f'/api/chat/rooms/{room.id}/add_member/',
            {'username': 'user2'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MessageTestCase(TestCase):
    """Test message endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.room = Room.objects.create(name='General', admin=self.user1)
        Membership.objects.create(user=self.user1, room=self.room)
        self.client.force_authenticate(user=self.user1)
    
    def test_send_message(self):
        """Test sending a message."""
        response = self.client.post(
            '/api/chat/messages/',
            {
                'room': self.room.id,
                'content': 'Hello everyone!'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Hello everyone!')
        self.assertEqual(response.data['sender'], self.user1.id)
    
    def test_list_messages(self):
        """Test listing messages."""
        Message.objects.create(
            room=self.room,
            sender=self.user1,
            content='Hello!'
        )
        
        response = self.client.get('/api/chat/messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_edit_message(self):
        """Test editing a message."""
        message = Message.objects.create(
            room=self.room,
            sender=self.user1,
            content='Hello!'
        )
        
        response = self.client.patch(
            f'/api/chat/messages/{message.id}/edit_message/',
            {'content': 'Updated message'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message.refresh_from_db()
        self.assertEqual(message.content, 'Updated message')
        self.assertTrue(message.is_edited)
    
    def test_delete_message(self):
        """Test deleting a message."""
        message = Message.objects.create(
            room=self.room,
            sender=self.user1,
            content='Hello!'
        )
        
        response = self.client.delete(
            f'/api/chat/messages/{message.id}/delete_message/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Message.objects.filter(id=message.id).exists())
    
    def test_add_reaction(self):
        """Test adding reaction to message."""
        message = Message.objects.create(
            room=self.room,
            sender=self.user1,
            content='Hello!'
        )
        
        response = self.client.post(
            f'/api/chat/messages/{message.id}/add_reaction/',
            {'emoji': '👍'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['emoji'], '👍')


class DirectMessageTestCase(TestCase):
    """Test direct message endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        self.client.force_authenticate(user=self.user1)
    
    def test_send_direct_message(self):
        """Test sending direct message."""
        response = self.client.post(
            '/api/chat/direct-messages/',
            {
                'recipient': self.user2.id,
                'content': 'Hi there!'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Hi there!')
        self.assertFalse(response.data['is_read'])
    
    def test_list_direct_messages(self):
        """Test listing direct messages."""
        DirectMessage.objects.create(
            sender=self.user1,
            recipient=self.user2,
            content='Hi!'
        )
        
        response = self.client.get('/api/chat/direct-messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_conversations(self):
        """Test getting conversations list."""
        DirectMessage.objects.create(
            sender=self.user1,
            recipient=self.user2,
            content='Hi!'
        )
        
        response = self.client.get('/api/chat/direct-messages/conversations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_get_conversation_with_user(self):
        """Test getting conversation with specific user."""
        DirectMessage.objects.create(
            sender=self.user1,
            recipient=self.user2,
            content='Hi!'
        )
        
        response = self.client.get(
            f'/api/chat/direct-messages/with_user/?user_id={self.user2.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_unread_count(self):
        """Test getting unread count."""
        DirectMessage.objects.create(
            sender=self.user2,
            recipient=self.user1,
            content='Hi!',
            is_read=False
        )
        
        response = self.client.get('/api/chat/direct-messages/unread_count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 1)


class UserPresenceTestCase(TestCase):
    """Test user presence endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_set_online(self):
        """Test setting user online."""
        response = self.client.post('/api/chat/presence/set_online/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'online')
        self.assertTrue(response.data['is_online'])
    
    def test_set_away(self):
        """Test setting user away."""
        response = self.client.post('/api/chat/presence/set_away/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'away')
        self.assertFalse(response.data['is_online'])
    
    def test_set_offline(self):
        """Test setting user offline."""
        response = self.client.post('/api/chat/presence/set_offline/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'offline')
        self.assertFalse(response.data['is_online'])
    
    def test_get_online_users(self):
        """Test getting online users."""
        UserPresence.objects.create(user=self.user, status='online', is_online=True)
        
        response = self.client.get('/api/chat/presence/online_users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)


class TypingIndicatorTestCase(TestCase):
    """Test typing indicator endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        self.room = Room.objects.create(name='General', admin=self.user)
        self.client.force_authenticate(user=self.user)
    
    def test_start_typing_room(self):
        """Test starting typing in room."""
        response = self.client.post(
            '/api/chat/typing/start_typing_room/',
            {'room_id': self.room.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['room'], self.room.id)
    
    def test_stop_typing(self):
        """Test stopping typing."""
        response = self.client.post(
            '/api/chat/typing/stop_typing/',
            {'room_id': self.room.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
