"""
Base App URL Configuration
"""

from django.urls import path
from . import views

app_name = 'base'

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('help/', views.help_page, name='help'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('safety/', views.safety, name='safety'),
    path('contact/', views.contact, name='contact'),
    path('categories/', views.browse_categories, name='categories'),
    path('categories/<str:category>/', views.browse_categories, name='categories_filtered'),

    # Admin dashboard
    path('site-admin/', views.admin_dashboard, name='admin_dashboard'),
    path('site-admin/api/stats/', views.admin_api_stats, name='admin_api_stats'),
    path('site-admin/api/users/', views.admin_api_users, name='admin_api_users'),
    path('site-admin/api/listings/', views.admin_api_listings, name='admin_api_listings'),
    path('site-admin/api/conversations/', views.admin_api_conversations, name='admin_api_conversations'),
    path('site-admin/api/users/<int:user_id>/action/', views.admin_api_user_action, name='admin_api_user_action'),
    path('site-admin/api/listings/<int:listing_id>/action/', views.admin_api_listing_action, name='admin_api_listing_action'),
    path('site-admin/api/reports/', views.admin_api_reports, name='admin_api_reports'),
    path('site-admin/api/reports/<int:report_id>/action/', views.admin_api_report_action, name='admin_api_report_action'),
    path('site-admin/api/transactions/', views.admin_api_transactions, name='admin_api_transactions'),
    path('site-admin/api/config/', views.admin_api_config_get, name='admin_api_config_get'),
    path('site-admin/api/config/save/', views.admin_api_config_save, name='admin_api_config_save'),
    path('site-admin/api/boosts/', views.admin_api_boosts, name='admin_api_boosts'),
    path('site-admin/api/boosts/<int:boost_id>/action/', views.admin_api_boost_action, name='admin_api_boost_action'),
    path('api/config/', views.public_config, name='public_config'),
    path('api/boost/initiate/', views.initiate_boost_payment, name='initiate_boost_payment'),
    path('api/boost/callback/', views.paystack_callback, name='paystack_callback'),
    path('api/boost/webhook/', views.paystack_webhook, name='paystack_webhook'),
]