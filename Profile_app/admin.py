from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Profile # Or whatever your profile model is named

admin.site.register(Profile)