from django.contrib import admin
from django.urls import path, include

# --- ADD THESE TWO IMPORTS ---
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('BlogApp.urls')),
]

# --- ADD THIS IF-STATEMENT AT THE END ---
# This tells Django to serve media files (like your cover image)
# when in DEBUG (development) mode.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)