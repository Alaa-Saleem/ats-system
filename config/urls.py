from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('', include('config.public_urls')),
    path('admin/', admin.site.urls),
    path('dashboard/', include('apps.dashboard.urls')),
    path('candidates/', include('apps.candidates.urls')),
    path('jobs/', include('apps.jobs.urls')),
    path('clients/', include('apps.clients.urls')),
    path('pipeline/', include('apps.pipeline.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('superadmin/', include('apps.superadmin.urls')),
    path('profiles/', include('apps.profiles.urls')),
    path('p/', include(('apps.profiles.urls', 'profiles_public'), namespace='profiles_public')),
)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
