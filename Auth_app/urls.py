
from django.urls import path
from . import views
from Profile_app import views as profile_views

app_name = 'auth'

urlpatterns = [
    path('', views.Auth_view, name='auth_view'),
    path('api/login/', views.login_view, name='api_login'),
    path('api/signup/', views.signup_api, name='api_signup'),
    path('2fa/', views.two_fa_page, name='two_fa_page'),
    path('api/verify-2fa/', views.verify_2fa_view, name='api_verify_2fa'),
    path('logout/', profile_views.logout_view, name='logout'),
    path('deactivate/', profile_views.deactivate_account, name='deactivate_account'),
    path('delete-account/', profile_views.delete_account, name='delete_account'),
]