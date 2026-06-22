from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat, name='chat'),
    path('api/conversations/', views.get_conversations, name='get_conversations'),
    path('api/messages/<int:conv_id>/', views.get_messages, name='get_messages'),
    path('api/start/', views.start_conversation, name='start_conversation'),
    path('api/start-direct/', views.start_direct, name='start_direct'),
    path('api/search-users/', views.search_users, name='search_users'),
    path('api/push-subscribe/', views.push_subscribe, name='push_subscribe'),
    path('api/push-unsubscribe/', views.push_unsubscribe, name='push_unsubscribe'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
]
