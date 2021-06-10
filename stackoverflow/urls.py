"""
Stackoverflow URL Configuration.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/http/urls/
"""

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import settings


urlpatterns = [
    path('hasker/', include('hasker.urls')),
    path('users/', include('users.urls')),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
