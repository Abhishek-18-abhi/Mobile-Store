from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.http import Http404, FileResponse
from pathlib import Path


def serve_media(request, path):
    # 1. Check runtime uploaded media in /tmp/media
    tmp_path = Path('/tmp') / 'media' / path
    if tmp_path.is_file():
        return FileResponse(open(tmp_path, 'rb'))
    
    # 2. Check bundled git repo media in BASE_DIR / media
    base_path = settings.BASE_DIR / 'media' / path
    if base_path.is_file():
        return FileResponse(open(base_path, 'rb'))

    raise Http404("Media file not found")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('products.urls')),
    path('accounts/', include('accounts.urls')),
    path('cart/', include('orders.urls')),
    path('payment/', include('payment.urls')),
    re_path(r'^media/(?P<path>.*)$', serve_media, name='serve_media'),
]
