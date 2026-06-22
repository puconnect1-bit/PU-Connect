"""
Main URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from Base_app.views import r2_presign, r2_upload, serve_sw, serve_offline

from django.views.generic import TemplateView


def handler429(request, exception=None):
    return JsonResponse({'status': 'error', 'message': 'Too many requests — please slow down.'}, status=429)


handler403 = handler429

urlpatterns = [
    # SEO
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('sitemap.xml', TemplateView.as_view(template_name="sitemap.xml", content_type="application/xml")),

    # Admin
    path('admin/', admin.site.urls),

    # PWA files served from root so SW scope covers /
    path('sw.js', serve_sw, name='sw'),
    path('offline/', serve_offline, name='offline'),

    # Base app (includes: home, about, help, terms, privacy, safety, contact)
    path('', include('Base_app.urls')),

    # Authentication
    path('auth/', include('Auth_app.urls')),

    # Main apps
    path('dashboard/', include('dash_app.urls')),
    path('listings/', include('Listings_app.urls')),
    path('profile/', include('Profile_app.urls')),
    path('chat/', include('chat_app.urls')),
    path('search/', include('search_app.urls')),
    path('reels/', include('Reels_app.urls')),
    path("accounts/", include("allauth.urls")),
    path('api/r2-presign/', r2_presign, name='r2_presign'),
    path('api/r2-upload/', r2_upload, name='r2_upload'),

]
# Media & Static files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)