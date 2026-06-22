from django.urls import path
from . import views

app_name = 'reels'

urlpatterns = [
    path('', views.reels, name='reels'),
]