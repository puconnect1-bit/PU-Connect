from django.db import models
from django.contrib.auth.models import User
from Listings_app.models import Listing

class Conversation(models.Model):
    """
    Represents a chat room between two or more users.
    Often tied to a specific product listing.
    """
    participants = models.ManyToManyField(User, related_name='conversations')
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        participant_names = ", ".join([user.username for user in self.participants.all()])
        return f"Chat between: {participant_names} (Listing: {self.listing.title if self.listing else 'None'})"

class Message(models.Model):
    """
    An individual message within a conversation.
    Supports text, images, and voice notes.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    
    # Content types
    text = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, max_length=500)
    voice_url = models.URLField(blank=True, null=True, max_length=500)
    voice_duration = models.PositiveIntegerField(default=0)
    meetup_spot = models.CharField(max_length=255, blank=True, null=True)
    meetup_time = models.CharField(max_length=100, blank=True, null=True)
    
    # Metadata
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender.username} at {self.timestamp}"

class PushSubscription(models.Model):
    """Stores Web Push subscription info per user/device."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.TextField(unique=True)
    p256dh = models.TextField()
    auth = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PushSub for {self.user.username}"

class Notification(models.Model):
    """
    User notifications for new messages, activity, etc.
    """
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('system', 'System Update'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='message')
    title = models.CharField(max_length=100)
    content = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"

