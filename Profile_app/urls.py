from django.urls import path
from . import views

app_name = 'profile'

urlpatterns = [
    path('', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('complete/', views.complete_profile, name='complete_profile'),
    path('api/me/', views.get_my_profile, name='get_my_profile'),
    path('api/update/', views.update_profile_api, name='update_profile'),
    path('api/user/<str:username>/', views.public_profile_api, name='public_profile_api'),
    path('api/followers/', views.followers_list, name='followers_list'),
    path('api/following/', views.following_list, name='following_list'),
    path('api/follow/<str:username>/', views.toggle_follow, name='toggle_follow'),
    path('api/report/<str:username>/', views.report_user, name='report_user'),
    path('verify/', views.verification_page, name='verification_page'),
    path('api/verification/info/', views.verification_info, name='verification_info'),
    path('api/verification/apply/', views.verification_apply, name='verification_apply'),
    path('api/verification/paid/', views.verification_paid, name='verification_paid'),
    path('api/verification/submit-docs/', views.verification_submit_docs, name='verification_submit_docs'),
    path('api/change-password/', views.change_password, name='change_password'),
    path('<str:username>/', views.public_profile_page, name='public_profile'),
]

